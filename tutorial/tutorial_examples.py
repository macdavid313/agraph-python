
from franz.openrdf.sail.sail import SailRepository
from franz.openrdf.repository.repository import Repository
from franz.openrdf.sail.allegrographstore import AllegroGraphStore
from franz.openrdf.query.query import QueryLanguage
from franz.openrdf.vocabulary.rdf import RDF
from franz.openrdf.vocabulary.xmlschema import XMLSchema
from franz.openrdf.query.dataset import Dataset
from franz.openrdf.rio.rdfformat import RDFFormat
from franz.openrdf.rio.rdfwriter import  NTriplesWriter
from franz.openrdf.rio.rdfxmlwriter import RDFXMLWriter


import os, urllib, datetime, time

CURRENT_DIRECTORY = os.getcwd() 

def test0():
    for i in range(0, 5):
        print "Hello World"
        time.sleep(5)

def test1():
    """
    Tests getting the repository up.  Is called by most of the other tests to do the startup.
    """
    sesameDir = "/Users/bmacgregor/Desktop/SesameFolder"
    store = AllegroGraphStore(AllegroGraphStore.RENEW, "localhost", "testP",
                              sesameDir, port=4567)
    myRepository = Repository(store)
    myRepository.initialize()
    print "Repository is up!"
    return myRepository
    
def test2():
    myRepository = test1()
    f = myRepository.getValueFactory()
    ## create some resources and literals to make statements out of
    alice = f.createURI("http://example.org/people/alice")
    bob = f.createURI("http://example.org/people/bob")
    name = f.createURI("http://example.org/ontology/name")
    person = f.createURI("http://example.org/ontology/Person")
    bobsName = f.createLiteral("Bob")
    alicesName = f.createLiteral("Alice")

    conn = myRepository.getConnection()
    ## alice is a person
    conn.add(alice, RDF.TYPE, person)
    ## alice's name is "Alice"
    conn.add(alice, name, alicesName)
    ## bob is a person
    conn.add(bob, RDF.TYPE, person)
    ## bob's name is "Bob":
    conn.add(bob, name, bobsName)
    print "Triple count: ", conn.size()
    conn.remove(bob, name, bobsName)
    print "Triple count: ", conn.size()
    conn.add(bob, name, bobsName)    
    return myRepository

def test3():    
    conn = test2().getConnection()
    try:
        queryString = "SELECT ?s ?p ?o  WHERE {?s ?p ?o .}"
        tupleQuery = conn.prepareTupleQuery(QueryLanguage.SPARQL, queryString)
        result = tupleQuery.evaluate();
        try:
            for bindingSet in result:
                s = bindingSet.getValue("s")
                p = bindingSet.getValue("p")
                o = bindingSet.getValue("o")              
                print "%s %s %s" % (s, p, o)
        finally:
            result.close();
    finally:
        conn.close();
        
def test4():
    myRepository = test2()
    conn = myRepository.getConnection()
    alice = myRepository.getValueFactory().createURI("http://example.org/people/alice")
    statements = conn.getStatements(alice, None, None, False)
    for s in statements:
        print s
    print "Same thing using JDBC:"
    resultSet = conn.getJDBCStatements(alice, None, None, False)
    while resultSet.next():
        #print resultSet.getRow()
        print "   ", resultSet.getValue(3), "   ", resultSet.getString(3)  
               
def test5():
    """
    Typed Literals
    """
    myRepository = test1()
    conn = myRepository.getConnection()
    f = myRepository.getValueFactory()
    conn.clear()
    exns = "http://example.org/people/"
    alice = f.createURI("http://example.org/people/alice")
    age = f.createURI(namespace=exns, localname="age")
    weight = f.createURI(namespace=exns, localname="weight")    
    favoriteColor = f.createURI(namespace=exns, localname="favoriteColor")
    birthdate = f.createURI(namespace=exns, localname="birthdate")
    ted = f.createURI(namespace=exns, localname="Ted")
    red = f.createLiteral('Red')
    rouge = f.createLiteral('Rouge', language="fr")
    fortyTwo = f.createLiteral('42', datatype=XMLSchema.INT)
    fortyTwoInteger = f.createLiteral('42', datatype=XMLSchema.LONG)    
    fortyTwoUntyped = f.createLiteral('42')
    date = f.createLiteral('1984-12-06', datatype=XMLSchema.DATE)     
    time = f.createLiteral('1984-12-06', datatype=XMLSchema.DATETIME)         
    stmt1 = f.createStatement(alice, age, fortyTwo)
    stmt2 = f.createStatement(ted, age, fortyTwoUntyped)    
    conn.add(stmt1)
    conn.addStatement(stmt2)
    conn.addTriple(alice, weight, f.createLiteral('20.5'))
    conn.addTriple(ted, weight, f.createLiteral('20.5', datatype=XMLSchema.FLOAT))
    conn.add(alice, favoriteColor, red)
    conn.add(ted, favoriteColor, rouge)
    conn.add(alice, birthdate, date)
    conn.add(ted, birthdate, time)    
    for obj in [None, fortyTwo, fortyTwoUntyped, f.createLiteral('20.5', datatype=XMLSchema.FLOAT), f.createLiteral('20.5'),
                red, rouge]:
        print "Retrieve triples matching '%s'." % obj
        statements = conn.getStatements(None, None, obj, False)
        for s in statements:
            print s
    for obj in ['42', '"42"', '20.5', '"20.5"', '"20.5"^^xsd:float', '"Rouge"@fr', '"1984-12-06"^^xsd:date']:
        print "Query triples matching '%s'." % obj
        queryString = """PREFIX xsd: <http://www.w3.org/2001/XMLSchema#> 
        SELECT ?s ?p ?o WHERE {?s ?p ?o . filter (?o = %s)}
        """ % obj
        tupleQuery = conn.prepareTupleQuery(QueryLanguage.SPARQL, queryString)
        result = tupleQuery.evaluate();    
        for bindingSet in result:
            s = bindingSet[0]
            p = bindingSet[1]
            o = bindingSet[2]
            print "%s %s %s" % (s, p, o)
    fortyTwoInt = f.createLiteral(42)
    print fortyTwoInt.toPython()

def test6():
    myRepository = test1()
    conn = myRepository.getConnection()
    conn.clear()   
    path1 = "./vc-db-1.rdf"    
    path2 = "./football.nt"            
    baseURI = "http://example.org/example/local"
    location = "/tutorial/vc_db_1_rdf" 
    context = myRepository.getValueFactory().createURI(location)
    conn.setNamespace("vcd", "http://www.w3.org/2001/vcard-rdf/3.0#");
    ## read football triples into the null context:
    conn.add(path2, base=baseURI, format=RDFFormat.NTRIPLES)
    ## read vcards triples into the context 'context':
    conn.addFile(path1, baseURI, format=RDFFormat.RDFXML, context=context);
    myRepository.indexTriples(all=True, asynchronous=False)
    print "After loading, repository contains %s vcard triples and %s football triples." % (conn.size(context), conn.size(None))
    return myRepository
        
def test7():    
    conn = test6().getConnection()
    queryString = "SELECT DISTINCT ?s ?c WHERE {graph ?c {?s ?p ?o .} }"
    tupleQuery = conn.prepareTupleQuery(QueryLanguage.SPARQL, queryString)
    result = tupleQuery.evaluate();
    for bindingSet in result:
        print bindingSet[0], bindingSet[1]
    conn.close()

import urlparse

def test8():
    myRepository = test6()
    conn = myRepository.getConnection()
    location = "/tutorial/vc_db_1_rdf" 
    context = myRepository.getValueFactory().createURI(location)
    outputFile = "/tmp/temp.nt"
    #outputFile = None
    if outputFile == None:
        print "Writing to Standard Out instead of to a file"
    ntriplesWriter = NTriplesWriter(outputFile)
    conn.export(ntriplesWriter, context);
    outputFile2 = "/tmp/temp.rdf"
    #outputFile2 = None
    if outputFile2 == None:
        print "Writing to Standard Out instead of to a file"
    rdfxmlfWriter = RDFXMLWriter(outputFile2)    
    conn.export(rdfxmlfWriter, context)

def test9():
    myRepository = test6()
    conn = myRepository.getConnection()
    conn.exportStatements(None, RDF.TYPE, None, False, RDFXMLWriter(None))

def test10():
    """
    Datasets and multiple contexts
    """
    myRepository = test1();
    conn = myRepository.getConnection()
    f = myRepository.getValueFactory()
    exns = "http://example.org/people/"
    alice = f.createURI(namespace=exns, localname="alice")
    bob = f.createURI(namespace=exns, localname="bob")
    ted = f.createURI(namespace=exns, localname="ted")
    person = f.createURI(namespace=exns, localname="Person")
    name = f.createURI(namespace=exns, localname="name")    
    alicesName = f.createLiteral("Alice")    
    bobsName = f.createLiteral("Bob")
    tedsName = f.createLiteral("Ted")    
    context1 = f.createURI(namespace=exns, localname="cxt1")      
    context2 = f.createURI(namespace=exns, localname="cxt2")          
    conn.add(alice, RDF.TYPE, person, context1)
    conn.add(alice, name, alicesName, context1)
    conn.add(bob, RDF.TYPE, person, context2)
    conn.add(bob, name, bobsName, context2)
    conn.add(ted, RDF.TYPE, person)
    conn.add(ted, name, bobsName)
    statements = conn.getStatements(None, None, None, False)
    print "All triples in all contexts:"
    for s in statements:
        print s
    statements = conn.getStatements(None, None, None, False, [context1, context2])
    print "Triples in contexts 1 and 2:"
    for s in statements:
        print s
    queryString = """
    SELECT ?s ?p ?o ?c
    WHERE { GRAPH ?c {?s ?p ?o . } } 
    """
    ds = Dataset()
    ds.addNamedGraph(context1)
    ds.addNamedGraph(context2)
    tupleQuery = conn.prepareTupleQuery(QueryLanguage.SPARQL, queryString)
    tupleQuery.setDataset(ds)
    result = tupleQuery.evaluate();    
    print "Query over contexts 1 and 2."
    for bindingSet in result:
        print bindingSet.getRow()
    queryString = """
    SELECT ?s ?p ?o    
    WHERE {?s ?p ?o . } 
    """
    ds = Dataset()
    ds.addDefaultGraph(None)
    tupleQuery = conn.prepareTupleQuery(QueryLanguage.SPARQL, queryString)
    tupleQuery.setDataset(ds)
    result = tupleQuery.evaluate();    
    print "Query over the null context."
    for bindingSet in result:
        print bindingSet.getRow()
    
def test11():
    """
    Namespaces
    """
    myRepository = test1();
    conn = myRepository.getConnection()
    f = myRepository.getValueFactory()
    exns = "http://example.org/people/"
    alice = f.createURI(namespace=exns, localname="alice")
    person = f.createURI(namespace=exns, localname="Person")
    conn.add(alice, RDF.TYPE, person)
    myRepository.indexTriples(all=True, asynchronous=True)
    conn.setNamespace('ex', exns)
    queryString = """
    SELECT ?s ?p ?o 
    WHERE { ?s ?p ?o . FILTER ((?p = rdf:type) && (?o = ex:Person) ) }
    """
    tupleQuery = conn.prepareTupleQuery(QueryLanguage.SPARQL, queryString)
    result = tupleQuery.evaluate();  
    print    
    for bindingSet in result:
        print bindingSet[0], bindingSet[1], bindingSet[2]

def test12():
    """
    Text search
    """
    myRepository = test1();
    conn = myRepository.getConnection()
    f = myRepository.getValueFactory()
    exns = "http://example.org/people/"
    conn.setNamespace('ex', exns)
    #myRepository.registerFreeTextPredicate("http://example.org/people/name")    
    myRepository.registerFreeTextPredicate(namespace=exns, localname='fullname')
    alice = f.createURI(namespace=exns, localname="alice1")
    persontype = f.createURI(namespace=exns, localname="Person")
    fullname = f.createURI(namespace=exns, localname="fullname")    
    alicename = f.createLiteral('Alice B. Toklas')
    book =  f.createURI(namespace=exns, localname="book1")
    booktype = f.createURI(namespace=exns, localname="Book")
    booktitle = f.createURI(namespace=exns, localname="title")    
    wonderland = f.createLiteral('Alice in Wonderland')
    conn.add(alice, RDF.TYPE, persontype)
    conn.add(alice, fullname, alicename)
    conn.add(book, RDF.TYPE, booktype)    
    conn.add(book, booktitle, wonderland) 
    ##myRepository.indexTriples(all=True, asynchronous=True)
    conn.setNamespace('ex', exns)
    #conn.setNamespace('fti', "http://franz.com/ns/allegrograph/2.2/textindex/")    
    queryString = """
    SELECT ?s ?p ?o
    WHERE { ?s ?p ?o . ?s fti:match 'Alice' . }
    """
#    queryxxString=""" 
#    SELECT ?s ?p ?o
#    WHERE { ?s ?p ?o . FILTER regex(?o, "Ali") }
#    """
    tupleQuery = conn.prepareTupleQuery(QueryLanguage.SPARQL, queryString)
    result = tupleQuery.evaluate(); 
    print "Query results"
    for bindingSet in result:
        print bindingSet

if __name__ == '__main__':
    choices = [i for i in range(1,17)]
    choices = [0]
    for choice in choices:
        print "\n==========================================================================="
        print "Test Run Number ", choice, "\n"
        if choice == 0: test0()
        elif choice == 1: test1()
        elif choice == 2: test2()
        elif choice == 3: test3()
        elif choice == 4: test4()    
        elif choice == 5: test5()        
        elif choice == 6: test6()            
        elif choice == 7: test7()                
        elif choice == 8: test8()                
        elif choice == 9: test9()                        
        elif choice == 10: test10()                            
        elif choice == 11: test11()
        elif choice == 12: test12()                                                                                   
        else:
            print "No such test exists."
    