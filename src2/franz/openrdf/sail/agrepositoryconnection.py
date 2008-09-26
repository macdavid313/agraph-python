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

import os

from franz.openrdf.exceptions import *
from franz.openrdf.sail.sail import Sail, SailConnection
from franz.openrdf.repository.repositoryresult import RepositoryResult
from franz.openrdf.repository.jdbcresultset import JDBCResultSet
from franz.openrdf.model.value import Value, URI, BNode, Namespace
from franz.openrdf.model.statement import Statement
from franz.openrdf.vocabulary.rdf import RDF
from franz.openrdf.vocabulary.rdfs import RDFS
from franz.openrdf.vocabulary.xmlschema import XMLSchema
from franz.openrdf.vocabulary.owl import OWL
from franz.openrdf.query.query import Query, TupleQuery, GraphQuery, BooleanQuery
from franz.allegrograph.directcalls import DirectCaller
from franz.allegrograph.upi import UPI
from franz.openrdf.rio.rdfformat import RDFFormat

# * Main interface for updating data in and performing queries on a Sesame
# * repository. By default, a RepositoryConnection is in autoCommit mode, meaning
# * that each operation corresponds to a single transaction on the underlying
# * store. autoCommit can be switched off in which case it is up to the user to
# * handle transaction commit/rollback. Note that care should be taking to always
# * properly close a RepositoryConnection after one is finished with it, to free
# * up resources and avoid unnecessary locks.
# * <p>
# * Several methods take a vararg argument that optionally specifies a (set of)
# * context(s) on which the method should operate. Note that a vararg parameter
# * is optional, it can be completely left out of the method call, in which case
# * a method either operates on a provided statements context (if one of the
# * method parameters is a statement or collection of statements), or operates on
# * the repository as a whole, completely ignoring context. A vararg argument may
# * also be 'null' (cast to Resource) meaning that the method operates on those
# * statements which have no associated context only.
# * <p>
# * Examples:
# * 
# * <pre>
# * // Ex 1: this method retrieves all statements that appear in either context1 or context2, or both.
# * RepositoryConnection.getStatements(null, null, null, true, context1, context2);
# * 
# * // Ex 2: this method retrieves all statements that appear in the repository (regardless of context).
# * RepositoryConnection.getStatements(null, null, null, true);
# * 
# * // Ex 3: this method retrieves all statements that have no associated context in the repository.
# * // Observe that this is not equivalent to the previous method call.
# * RepositoryConnection.getStatements(null, null, null, true, (Resource)null);
# * 
# * // Ex 4: this method adds a statement to the store. If the statement object itself has 
# * // a context (i.e. statement.getContext() != null) the statement is added to that context. Otherwise,
# * // it is added without any associated context.
# * RepositoryConnection.add(statement);
# * 
# * // Ex 5: this method adds a statement to context1 in the store. It completely ignores any
# * // context the statement itself has.
# * RepositoryConnection.add(statement, context1);
 

class AllegroGraphRepositoryConnection(SailConnection):
    def __init__(self, store):
        self.sail_store = store 
        self.mini_repository = store.mini_repository
        self.is_closed = False
    
    def rollback(self):
        print "PRETENDING TO ROLLBACK"
    
    def close(self):
        self.is_closed = True
    
    def commit(self):
        print "PRETENDING TO COMMIT"
    
    def prepareQuery(self, queryLanguage, queryString, baseURI=None):
        """
        Parse 'queryString' into a query object which can be
        executed against the RDF storage.
        """
        ## THIS IS BOGUS:
        return Query(queryString, queryLanguage, baseURI)

    def prepareTupleQuery(self, queryLanguage, queryString, baseURI=None):
        """
        Parse 'queryString' into a query object which can be
        executed against the RDF storage.  'queryString' must be a SELECT
        query.  The result of query
        execution is an iterator of tuples.
        """
        query = TupleQuery(queryLanguage, queryString, baseURI=baseURI)
        query.setConnection(self)
        return query

    def prepareGraphQuery(self, queryLanguage, queryString, baseURI=None):
        """
        Parse 'queryString' into a query object which can be
        executed against the RDF storage.  'queryString' must be a CONSTRUCT
        or DESCRIBE query.  The result of query
        execution is an iterator of statements/quads.
        """
        query = GraphQuery(queryLanguage, queryString, baseURI=baseURI)
        query.setDirectCaller(self.directCaller)
        return query

    def prepareBooleanQuery(self, queryLanguage, queryString, baseURI=None):
        """
        Parse 'queryString' into a query object which can be
        executed against the RDF storage.  'queryString' must be an ASK
        query.  The result is true or false.
        """
        query = BooleanQuery(queryLanguage, queryString, baseURI=baseURI)
        query.setDirectCaller(self.directCaller)
        return query



#     * Returns the number of (explicit) statements that are in the specified
#     * contexts in this repository.
#     * 
#     * @param contexts
#     *        The context(s) to get the data from. Note that this parameter is a
#     *        vararg and as such is optional. If no contexts are supplied the
#     *        method operates on the entire repository.
#     * @return The number of explicit statements from the specified contexts in
#     *         this repository.
    def size(self, contexts=[]):
        """
        Returns the number of (explicit) statements that are in the specified
        contexts in this repository.
        """
        if contexts == []:
            self.mini_repository.getSize()
        else:
            print "Computing the size of a context is currently very expensive"
            resultSet = self.getJDBCStatements(None, None, None, contexts)
            count = 0
            while resultSet.next():
                count += 1
            return count
                

#     * Returns <tt>true</tt> if this repository does not contain any (explicit)
#     * statements.
#     * 
#     * @return <tt>true</tt> if this repository is empty, <tt>false</tt>
#     *         otherwise.
#     * @throws RepositoryException
#     *         If the repository could not be checked to be empty.
    def isEmpty(self):
        return self.size() == 0
       


#     * Gets all statements with a specific subject, predicate and/or object from
#     * the repository. The result is optionally restricted to the specified set
#     * of named contexts.
#     * 
#     * @param subj
#     *        A Resource specifying the subject, or <tt>null</tt> for a
#     *        wildcard.
#     * @param pred
#     *        A URI specifying the predicate, or <tt>null</tt> for a wildcard.
#     * @param obj
#     *        A Value specifying the object, or <tt>null</tt> for a wildcard.
#     * @param contexts
#     *        The context(s) to get the data from. Note that this parameter is a
#     *        vararg and as such is optional. If no contexts are supplied the
#     *        method operates on the entire repository.
#     * @param includeInferred
#     *        if false, no inferred statements are returned; if true, inferred
#     *        statements are returned if available. The default is true.
#     * @return The statements matching the specified pattern. The result object
#     *         is a {@link RepositoryResult} object, a lazy Iterator-like object
#     *         containing {@link Statement}s and optionally throwing a
#     *         {@link RepositoryException} when an error when a problem occurs
#     *         during retrieval.
    #RepositoryResult<Statement> 
    def getStatements(self, subj, pred,  obj, contexts=[], includeInferred=False):
        """
        Gets all statements with a specific subject, predicate and/or object from
        the repository. The result is optionally restricted to the specified set
        of named contexts.  Returns a RepositoryResult that produces a 'Statement'
        each time that 'next' is called.
        """
        obj = self.sail_store.getValueFactory().object_position_term_to_openrdf_term(obj, predicate=pred)
        if not isinstance(contexts, list):
            contexts = [contexts]
        stringTuples = self.mini_repository.getStatements(subj, pred, obj, contexts, infer=includeInferred)
        return RepositoryResult(stringTuples)
       
    def getJDBCStatements(self, subj, pred,  obj, contexts=[], includeInferred=False):
        """
        Gets all statements with a specific subject, predicate and/or object from
        the repository. The result is optionally restricted to the specified set
        of named contexts.  Returns a JDBCResultSet that enables Values, strings, etc.
        to be selectively extracted from the result, without the bulky overhead
        of the OpenRDF BindingSet protocol.
        """
        if not isinstance(contexts, list):
            contexts = [contexts]
        stringTuples = self.mini_repository.getStatements(subj, pred, obj, contexts, infer=includeInferred)
        return JDBCResultSet(stringTuples)

    def add(self, arg0, arg1=None, arg2=None, contexts=None, base=None, format=None):
        """
        Calls addTriple, addStatement, or addFile.  If 'contexts' is not
        specified, adds to the null context.
        """
        if contexts and not isinstance(contexts, list):
            contexts = [contexts]
        if isinstance(arg0, (str, file)):
            if contexts:
                if len(contexts) > 1:
                    raise IllegalArgumentException("Only one context may be specified when loading from a file.")
                context = contexts[0]
            else:
                context = None
            return self.addFile(arg0, base=base, format=format, context=context)
        elif isinstance(arg0, Value):
            return self.addTriple(arg0, arg1, arg2, contexts=contexts)
        elif isinstance(arg0, Statement):
            return self.addStatement(arg0, contexts=contexts)
        elif hasattr(arg0, '__iter__'):
            for s in arg0:
                self.addStatement(s, contexts=contexts)
        else:
            raise IllegalArgumentException("Illegal first argument to 'add'.  Expected a Value, Statement, File, or string.")
            
    def addFile(self, filePath, base=None, format=None, context=None):
        """
        Load the file or file path 'filePath' into the store.  'base' optionally defines a base URI,
        'format' is RDFFormat.NTRIPLES or RDFFormat.RDFXML, and 'context' optionally specifies
        which context the triples will be loaded into.
        """
        if isinstance(filePath, file):
            filePath = os.path.abspath(filePath.name)
        elif isinstance(filePath, str):
            if not filePath.startswith('/') and not filePath.lower().startswith('c:') and not filePath.lower().startswith("http:"):
                ## looks like its a relative file path; test to see if there is a local file that matches.
                ## If so, generate an absolute path name to enable AG server to read it:
                if os.path.exists(os.path.abspath(filePath)):
                    filePath = os.path.abspath(filePath)                    
        contextString = self.directCaller.canonicalize_context_argument(context)
        if format == RDFFormat.NTRIPLES or filePath.lower().endswith('.nt'):
            ## PASSING "NTRIPLE" AS 'ext' ARG FAILS HERE.  THE DOCUMENTATION DOESN'T
            ## SAY WHAT THE ACCEPTABLE VALUE(S) ARE:
            self.internal_ag_store.verifyEnabled().loadNTriples(self.internal_ag_store, filePath, contextString, None, None, None, None)
        elif format == RDFFormat.RDFXML or filePath.lower().endswith('.rdf') or filePath.lower().endswith('.owl'):
            self.internal_ag_store.verifyEnabled().loadRDF(self.internal_ag_store, filePath, contextString, base, None)
        else:
            raise Exception("Failed to specify a format for the file '%s'." % filePath)
        
    def _contexts_to_ntriple_contexts(self, contexts):
        if isinstance(contexts (list, tuple)):
            cxts = [c.toNTriples for c in contexts]
        elif contexts:
            cxts = contexts.toNTriples
        else:
            cxts = None
            return cxts
        
    def addTriple(self, subject, predicate, object, contexts=None):
        """
        Add the supplied triple of values to this repository, optionally to
        one or more named contexts.        
        """       
        self.mini_repository.addStatement(subject.toNTriples(), predicate.toNTriples(), object.toNTriples(),
                                          self._contexts_to_ntriple_contexts(contexts))
        
    def addTriples(self, triples_or_quads, context=None):
        """
        Add the supplied triples or quads to this repository.  Each triple can
        be a list or a tuple of Values.   If 'context' is set, then 
        the first argument must contain only triples, and each is inserted into
        the designated context.
        
        TODO: CONSIDER ALLOWING LISTS OF NTRIPLES STRINGS AS INPUT HERE
        """
        quads = []
        for q in triples_or_quads:
            quad = [None] * 4
            if isinstance(quad, (list, tuple)):
                quad[0] = q[0].toNTriples()
                quad[1] = q[1].toNTriples()
                quad[2] = q[2].toNTriples()
                quad[3] = q[3].toNTriples() if q[3] else self._contexts_to_ntriple_contexts(context)
            else:
                quad[0] = q.getSubject().toNTriples()
                quad[1] = q.getPredicate().toNTriples()
                quad[2] = q.getObject().toNTriples()
                quad[3] = q.getContext().toNTriples() if q.getContext() else self._contexts_to_ntriple_contexts(context)
                
#     * Adds the supplied statement to this repository, optionally to one or more
#     * named contexts.
#     * 
#     * @param st
#     *        The statement to add.
#     * @param contexts
#     *        The contexts to add the statements to. Note that this parameter is
#     *        a vararg and as such is optional. If no contexts are specified, the
#     *        statement is added to any context specified in each statement, or
#     *        if the statement contains no context, it is added without context.
#     *        If one or more contexts are specified the statement is added to
#     *        these contexts, ignoring any context information in the statement
#     *        itself.
#     * @throws RepositoryException
#     *         If the statement could not be added to the repository, for example
#     *         because the repository is not writable.


    def addStatement(self, statement, contexts=None):
        """
        Add the supplied statement to the specified contexts in the repository.
        """        
        self.addTriple(statement.getSubject(), statement.getPredicate(), statement.getObject(),
                       contexts=contexts)      

    def remove(self, arg0, arg1=None, arg2=None, contexts=None):
        """
        Remove the supplied triple of values from this repository, optionally to
        one or more named contexts.
        """
        if contexts and not isinstance(contexts, list):
            contexts = [contexts]
        if isinstance(arg0, Value) or arg0 is None: self.removeTriples(arg0, arg1, arg2, contexts=contexts)
        elif isinstance(arg0, Statement): self.removeStatement(arg0, contexts=contexts)
        elif hasattr(arg0, '__iter__'):
            for s in arg0:
                self.removeStatement(s, contexts=contexts)
        else:
            raise IllegalArgumentException("Illegal first argument to 'remove'.  Expected a Value, Statement, or iterator.")

    def removeTriples(self, subject, predicate, object, contexts=None):
        """
        Removes the statement(s) with the specified subject, predicate and object
        from the repository, optionally restricted to the specified contexts.
        """
        mgr = self.term2internal
        ## tricky: we need to distinguish between the null context (None) and
        ## all contexts '[]':
        if contexts is None:
            contexts = mgr.nullContextObject()
        elif isinstance(contexts, list) and not contexts:
            ## THIS IS *NOT* A NICE OPTION, BUT I HATE THE SESAME CONVENTION EVEN MORE - RMM
            contexts = mgr.wildValue()
        internalStore = mgr.internal_ag_store
        s = mgr.openTermToInternalStringTermOrWild(subject)
        p = mgr.openTermToInternalStringTermOrWild(predicate)
        object = self.sail_store.getValueFactory().object_position_term_to_openrdf_term(object, predicate=predicate)
        o = mgr.openTermToInternalStringTermOrWild(object)
        internalDirectConnector = internalStore.verifyEnabled()
        if contexts in [mgr.nullContextObject(), mgr.wildValue()]:
            internalDirectConnector.delete(internalStore, s, p, o, contexts, True)
        elif isinstance(contexts, list):
            for c in contexts:
                internalDirectConnector.delete(internalStore, s, p, o, mgr.openTermToInternalStringTerm(c), True)
        else:  ## assume 'contexts' is a single context:
            internalDirectConnector.delete(internalStore, s, p, o, mgr.openTermToInternalStringTerm(contexts), True)


   
#     * Removes the supplied statement from the specified contexts in the
#     * repository.
#     * @param st
#     *        The statement to remove.
#     * @param contexts
#     *        The context(s) to remove the data from. Note that this parameter is
#     *        is optional. If no contexts are supplied the
#     *        method operates on the contexts associated with the statement
#     *        itself, and if no context is associated with the statement, on the
#     *        entire repository.
#     * @throws RepositoryException
#     *         If the statement could not be removed from the repository, for
#     *         example because the repository is not writable.
    def removeStatement(self, statement, contexts=None):
        """
        Removes the supplied statement(s) from the specified contexts in the repository.
        """
        self.removeTriples(statement.getSubject(), statement.getPredicate(), statement.getContext(), contexts=contexts)

#     * Removes all statements from a specific contexts in the repository.
#     * 
#     * @param contexts
#     *        The context(s) to remove the data from. Note that this parameter is
#     *        a vararg and as such is optional. If no contexts are supplied the
#     *        method operates on the entire repository.
#     * @throws RepositoryException
#     *         If the statements could not be removed from the repository, for
#     *         example because the repository is not writable.
    def clear(self, contexts=None):
        """
        Removes all statements from designated contexts in the repository.  If
        'contexts' is None, clears the repository of all statements.
        """
        self.removeTriples(None, None, None, contexts=contexts)
         
    ## Exports all explicit statements in the specified contexts to the supplied
    ## RDFHandler.
    ## 
    ## @param contexts
    ##        The context(s) to get the data from. Note that this parameter is a
    ##        vararg and as such is optional. If no contexts are supplied the
    ##        method operates on the entire repository.
    ## @param handler
    ##        The handler that will handle the RDF data.
    def export(self, handler, contexts=[]):
        self.exportStatements(None, None, None, False, handler, contexts=contexts)

    def exportStatements(self, subj, pred, obj, includeInferred, handler, contexts=None):
        """
        Exports all statements with a specific subject, predicate and/or object
        from the repository, optionally from the specified contexts.        
        """
        for prefix, name in self._get_namespaces_map().iteritems():
            handler.handleNamespace(prefix, name)
        statements = self.getStatements(subj, pred, obj, contexts, includeInferred=includeInferred)
        handler.export(statements)
      
    
    #############################################################################################
    ## In-memory implementation of namespaces
    #############################################################################################
    
    NAMESPACES_MAP = {}
    
    def _get_namespaces_map(self):
        map = AllegroGraphRepositoryConnection.NAMESPACES_MAP
        if not map:
            map.update({"rdf": RDF.NAMESPACE, 
                        "rdfs": RDFS.NAMESPACE,
                        "xsd": XMLSchema.NAMESPACE,
                        "owl": OWL.NAMESPACE, 
                        "fti": "http://franz.com/ns/allegrograph/2.2/textindex/",                                             
                        })
        return map
    
    ## Gets all declared namespaces as a RepositoryResult of {@link Namespace}
    def getNamespaces(self):
        return [Namespace(prefix, name) for prefix, name in self._get_namespaces_map().iteritems()]

    ## Gets the namespace that is associated with the specified prefix, if any.
    def getNamespace(self, prefix):
        name = self._get_namespaces_map().get(prefix.lower())
        if name: return Namespace(prefix.lower(), name)

    ## Sets the prefix for a namespace.
    def setNamespace(self, prefix, name):
        self._get_namespaces_map()[prefix.lower()] = name

    ## Removes a namespace declaration by removing the association between a
    ## prefix and a namespace name.
    def removeNamespace(self, prefix):
        self._get_namespaces_map()[prefix] = None

    ## Removes all namespace declarations from the repository.
    def clearNamespaces(self):
        self._get_namespaces_map().clear()


