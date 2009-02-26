#!/usr/bin/env python
# -*- coding: utf-8 -*-

##***** BEGIN LICENSE BLOCK *****
##Version: MPL 1.1
##
##The contents of this file are subject to the Mozilla Public License Version
##1.1 (the "License"); you may not use this file except in compliance with
##the License. You may obtain a copy of the License at
##http:##www.mozilla.org/MPL/
##
##Software distributed under the License is distributed on an "AS IS" basis,
##WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
##for the specific language governing rights and limitations under the
##License.
##
##The Original Code is the AllegroGraph Java Client interface.
##
##The Original Code was written by Franz Inc.
##Copyright (C) 2006 Franz Inc.  All Rights Reserved.
##
##***** END LICENSE BLOCK *****


from franz.openrdf.exceptions import *
from franz.openrdf.query import commonlogic
from franz.openrdf.query.dataset import ALL_CONTEXTS, Dataset
from franz.openrdf.query.queryresult import GraphQueryResult, TupleQueryResult
from franz.openrdf.repository.jdbcresultset import JDBCResultSet

class QueryLanguage:
    registered_languages = []
    SPARQL = None
    PROLOG = None
    COMMON_LOGIC = None
    def __init__(self, name):
        self.name = name
        QueryLanguage.registered_languages.append(self)
        
    def __str__(self): return self.name
    
    def getName(self): return self.name

    @staticmethod
    def values(): return QueryLanguage.registered_languages[:]
    
    @staticmethod
    def valueOf(name): 
        for ql in QueryLanguage.registered_languages:
            if ql.name.lower() == name.lower():
                return ql
        return None
    
QueryLanguage.SPARQL = QueryLanguage('SPARQL')
QueryLanguage.PROLOG = QueryLanguage('PROLOG')
QueryLanguage.COMMON_LOGIC = QueryLanguage('COMMON_LOGIC')

#############################################################################
##
#############################################################################

class Query(object):
    """
    A query on a {@link Repository} that can be formulated in one of the
    supported query languages (for example SeRQL or SPARQL). It allows one to
    predefine bindings in the query to be able to reuse the same query with
    different bindings.
    """
    def __init__(self, queryLanguage, queryString, baseURI=None):
        self.queryLanguage = queryLanguage
        self.queryString = queryString
        self.baseURI = baseURI
        self.dataset = None
        self.includeInferred = False
        self.bindings = {}
        self.connection = None
        ## CommonLogic parameters:
        self.preferred_execution_language = None
        self.actual_execution_language = None
        self.subject_comes_first = False

    def setBinding(self, name, value):
        """
        Binds the specified variable to the supplied value. Any value that was
        previously bound to the specified value will be overwritten.
        """
        if isinstance(value, str):
            value = self.connection.createLiteral(value)
        self.bindings[name] = value
        
    def setBindings(self, dict):
        if not dict: return
        for key, value in dict.iteritems():
            self.setBinding(key, value)

    def removeBinding(self, name):
        """ 
        Removes a previously set binding on the supplied variable. Calling this
        method with an unbound variable name has no effect.
        """ 
        if self.bindings.get(name):
            del self.bindings[name]

    def getBindings(self):
        """
        Retrieves the bindings that have been set on this query. 
        """ 
        return self.bindings

    def setDataset(self, dataset):
        """
        Specifies the dataset against which to evaluate a query, overriding any
        dataset that is specified in the query itself. 
        """ 
        self.dataset = dataset
     
    def getDataset(self):
        """
        Gets the dataset that has been set.
        """ 
        return self.dataset
    
    def setContexts(self, contexts):
        """
        Assert a set of contexts (named graphs) that filter all triples.
        """
        if not contexts: return
        ds = Dataset()
        for cxt in contexts:
            if str(cxt): cxt = self.connection.createURI(cxt)
            ds.addNamedGraph(cxt)
        self.setDataset(ds)
     
    def setIncludeInferred(self, includeInferred):
        """
        Determine whether evaluation results of this query should include inferred
        statements (if any inferred statements are present in the repository). The
        default setting is 'true'. 
        """ 
        self.includeInferred = includeInferred

    def getIncludeInferred(self):
        """
        Returns whether or not this query will return inferred statements (if any
        are present in the repository). 
        """ 
        return self.includeInferred
    
    def setConnection(self, connection):
        """
        Internal call to embed the connection into the query.
        """
        self.connection = connection
    
    TEMPORARY_ENUMERATION_RESOURCE = 'http://www.franz.com#TeMpOrArYeNuMeRaTiOn'
    
    def insert_temporary_enumerations(self, temporary_enumerations, insert_or_retract, contexts):
        """
        Enormous hack to circumvent AG's (SPARQL's) lack of a membership operator.
        """
        if not temporary_enumerations: return
        conn = self.connection
        context = conn.createURI(contexts[0]) if contexts else None
        print "insert_temporary_enumerations", context
        for tempRelationURI, enumeratedValues in temporary_enumerations.iteritems():
            quads = []
            for v in enumeratedValues:
                val = conn.createURI(v) if v and v[0] == '<' else conn.createLiteral(v)
                quads.append((conn.createURI(Query.TEMPORARY_ENUMERATION_RESOURCE), conn.createURI(tempRelationURI), val, context))
        if insert_or_retract == 'INSERT':
            #print "INSERTING TEMPORARY ENUMERATION TRIPLES", [(str(t[0]), str(t[1]), str(t[2])) for t in quads]
            conn.addTriples(quads)
        else:
            conn.removeQuads(quads)
    
    def evaluate_generic_query(self):
        """
        Evaluate a SPARQL or PROLOG or COMMON_LOGIC query, which may be a 'select', 'construct', 'describe'
        or 'ask' query (in the SPARQL case).  Return an appropriate response.
        """
        ##if self.dataset and self.dataset.getDefaultGraphs() and not self.dataset.getDefaultGraphs() == ALL_CONTEXTS:
        ##    raise UnimplementedMethodException("Query datasets not yet implemented for default graphs.")
        namedContexts = self.connection._contexts_to_ntriple_contexts(
                        self.dataset.getNamedGraphs() if self.dataset else None)
        regularContexts = self.connection._contexts_to_ntriple_contexts(
                self.dataset.getDefaultGraphs() if self.dataset else ALL_CONTEXTS)
        bindings = None
        if self.bindings:
            bindings = {}
            for vbl, val in self.bindings.items():
                bindings[vbl] = self.connection._convert_term_to_mini_term(val)
        mini = self.connection.mini_repository
        if self.queryLanguage == QueryLanguage.SPARQL:            
            query = splicePrefixesIntoQuery(self.queryString, self.connection)
            response = mini.evalSparqlQuery(query, context=regularContexts, namedContext=namedContexts, 
                                            infer=self.includeInferred, bindings=bindings)            
        elif self.queryLanguage == QueryLanguage.PROLOG:
            if namedContexts:
                raise QueryMissingFeatureException("Prolog queries do not the datasets (named graphs) option.")
            query = expandPrologQueryPrefixes(self.queryString, self.connection)
            response = mini.evalPrologQuery(query, infer=self.includeInferred)
        elif self.queryLanguage == QueryLanguage.COMMON_LOGIC:
            query, contexts, temporary_enumerations, lang, exception = commonlogic.translate_common_logic_query(self.queryString,
                                    preferred_language=self.preferred_execution_language, contexts=namedContexts)
            if contexts and not namedContexts:
                namedContexts = [uri.getURI() for uri in commonlogic.contexts_to_uris(contexts, self.connection)]
            self.actual_execution_language = lang ## for debugging
            if lang == 'SPARQL':
                print "         SPARQL QUERY", query
                query = splicePrefixesIntoQuery(query, self.connection)
                self.insert_temporary_enumerations(temporary_enumerations, 'INSERT', namedContexts)
                response = mini.evalSparqlQuery(query, context=regularContexts, namedContext=namedContexts, 
                                                infer=self.includeInferred, bindings=bindings)
                self.insert_temporary_enumerations(temporary_enumerations, 'RETRACT', namedContexts)            
            elif lang == 'PROLOG':
                if namedContexts:
                    raise QueryMissingFeatureException("Prolog queries do not the datasets (named graphs) option.")
                query = expandPrologQueryPrefixes(query, self.connection)
                print "         PROLOG QUERY", query
                response = mini.evalPrologQuery(query, infer=self.includeInferred)
            else:
                raise exception
        return response

    @staticmethod
    def _check_language(queryLanguage):
        if queryLanguage == 'SPARQL': return QueryLanguage.SPARQL
        elif queryLanguage == 'PROLOG': return QueryLanguage.PROLOG
        elif queryLanguage == 'COMMON_LOGIC': return QueryLanguage.COMMON_LOGIC        
        if not queryLanguage in [QueryLanguage.SPARQL, QueryLanguage.PROLOG, QueryLanguage.COMMON_LOGIC]:
            raise IllegalOptionException("Can't evaluate the query language '%s'.  Options are: SPARQL, PROLOG, and COMMON_LOGIC."
                                         % queryLanguage)
        return queryLanguage
            
  

#############################################################################
##
#############################################################################

def splicePrefixesIntoQuery(query, connection):
    """
    Add build-in and registered prefixes to 'query' when needed.
    """
    lcQuery = query.lower()
    referenced = []
    for prefix, ns in connection.getNamespaces().iteritems():
        if lcQuery.find(prefix) >= 0 and lcQuery.find("prefix %s" % prefix) < 0:
            referenced.append((prefix, ns))
    for ref in referenced:
        query = "PREFIX %s: <%s> %s" % (ref[0], ref[1], query)
    return query

def helpExpandPrologQueryPrefixes(query, connection, startPos):
    """
    Convert qnames in 'query' that match prefixes with declared namespaces into full URIs.
    """
    if startPos >= len(query): return query
    lcQuery = query.lower()
    bangPos = lcQuery[startPos:].find('!')
    if bangPos >= 0:
        bangPos = bangPos + startPos
        startingAtBang = lcQuery[bangPos:]
        if len(startingAtBang) > 1 and startingAtBang[1] == '<':
            ## found a fully-qualified namespace; skip past it
            endPos = startingAtBang.find('>')
            if endPos < 0: return query ## query is illegal, but that's not our problem
            return helpExpandPrologQueryPrefixes(query, connection, bangPos + endPos + 1)
        colonPos = startingAtBang.find(':')
        if colonPos >= 0:
            colonPos = bangPos + colonPos
            prefix = lcQuery[bangPos + 1:colonPos]
            ns = connection.getNamespace(prefix)
            if ns:
                for i, c in enumerate(lcQuery[colonPos + 1:]):
                    if not (c.isalnum() or c in ['_', '.', '-']): break
                endPos = colonPos + i + 1 if i else len(query) + 1
                localName = query[colonPos + 1: endPos]
                query = query.replace(query[bangPos + 1:endPos], "<%s%s>" % (ns, localName))
                return helpExpandPrologQueryPrefixes(query, connection, endPos)
    return query

def expandPrologQueryPrefixes(query, connection):
    """
    Convert qnames in 'query' that match prefixes with declared namespaces into full URIs.
    This assumes that legal chars in local names are alphanumerics and underscore and period.
    """
    query = helpExpandPrologQueryPrefixes(query, connection, 0)
    #print "AFTER EXPANSION", query
    return query

class TupleQuery(Query):
    def __init__(self, queryLanguage, queryString, baseURI=None):
        queryLanguage = Query._check_language(queryLanguage)
        super(TupleQuery, self).__init__(queryLanguage, queryString, baseURI=baseURI)
        self.connection = None
        
    def evaluate(self, jdbc=False):
        """
        Execute the embedded query against the RDF store.  Return
        an iterator that produces for each step a tuple of values
        (resources and literals) corresponding to the variables
        or expressions in a 'select' clause (or its equivalent).
        If 'jdbc', returns a JDBC-style iterator that miminizes the
        overhead of creating response objects.         
        """
        response = self.evaluate_generic_query()
        if jdbc:
            return JDBCResultSet(response['values'], column_names = response['names'])
        else:
            return TupleQueryResult(response['names'], response['values'])

class GraphQuery(Query):
    
    def evaluate(self):
        """
        Execute the embedded query against the RDF store.  Return
        a graph.
        """
        response = self.evaluate_generic_query()
        return GraphQueryResult(response)

class BooleanQuery(Query):
    
    def evaluate(self):
        """
        Execute the embedded query against the RDF store.  Return
        True or False
        """
        return self.evaluate_generic_query()


