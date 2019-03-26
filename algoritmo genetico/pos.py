import numpy as np
import copy
import matplotlib.pyplot as plt


letras = ["A","B","C","D","E","F","G","H"]

n=100
crimen = 3
min_porcent = 0.1

lamda={"A":0,"B":0.05,"C":0.5}
psi=0.9
nu=0.85
tipo="shg"
modelo="g_m_v" ## "g_1_v"


def read(file):
    # read the network
    filepath = file
    vertices = [];
    edges = [];
    readVertices = 0;
    readEdges = 0;
    with open(filepath) as fp:  
        line = fp.readline()
        cnt = 1
        while line:
            #print("Line {}: {}".format(cnt, line.strip()))

            if readVertices == 1:
                vertexData = line.strip().split(';');
                if len(vertexData)==4:
                    idxGroup = int(vertexData[3]);
                    vertices.append([int(vertexData[0]),idxGroup])

            if readEdges == 1:
                edgeData = line.strip().split(';');
                if len(edgeData)==2:
                    edges.append([int(edgeData[0]),int(edgeData[1])])
                    vertices[int(edgeData[0])].append(int(edgeData[1]));


            if line.strip() == '# Vertices':
#                 print('read vertices')
                readVertices = 1;
            if line.strip() == '# Edges':
                readVertices = 0;
                readEdges = 1;
#                 print('read edge')
            line = fp.readline()
            cnt += 1
            line.strip() 
    #array con 1 elemento: numero vertice, 2 elemento: grupo que se encuentra
    # resto son los vertices con los que se comunica
    #print(edges)
    for v in vertices:
        v[1]=letras[v[1]]
    return vertices,edges

def porcentaje(vecinos):
    P={}
    for v in vecinos:
        if not v[1] in P:
            P[v[1]]=0
        P[v[1]]+=1.0/len(vecinos)
        
    return P


def sumar_lista(A):
    result=[]
    for a in A:
        result+=a
    return result


def convert_state_to_vecinos(state,dist_crimen,n=n):
    vecinos=[[i,c] for i,c in zip(range(n),dist_crimen)]
    for i in range(1,n):
        k=sum([j for j in range(n-i+1,n)])
        m=sum([j for j in range(n-i,n)])

        v=state[k:m]

        for j in range(len(v)):
            if v[j] == 1 :
                vecinos[i-1].append(j+i)
                vecinos[j+i].append(i-1)
    return vecinos  


def convert_vertices_to_graph(vertices):
    import networkx as nx
    G = nx.Graph()
    for i in vertices:
        G.add_node(i[0],crime=i[1])
    edges=[]
    for i in vertices:
        for j in i[2:]:
            if (i[0],j) in edges or (j,i[0]) in edges:
                pass
            else:
                edges.append((i[0],j))
    G.add_edges_from(edges)
    return G


def validar_estado(estado,n=n):
    import networkx as nx
    
    vecinos=[[i,"A"] for i in range(n)]
    for i in range(1,n):
        k=sum([j for j in range(n-i+1,n)])
        m=sum([j for j in range(n-i,n)])

        v=estado[k:m]

        for j in range(len(v)):
            if v[j] == 1 :
                vecinos[i-1].append(j+i)
                vecinos[j+i].append(i-1)
    
    G=convert_vertices_to_graph(vecinos)
    
    return nx.is_connected(G)
    




def generate_estate(n=n,p=None):
    if not p :
        p=np.random.rand()
    total=n*(n-1)/2
    estado=np.ndarray.tolist(np.random.binomial(n=1,p=p,size=total))
    contador=0
    while validar_estado(estado=estado,n=n) == False:
        if contador > 100:
            p=np.random.rand()
            contador=0
        estado=np.ndarray.tolist(np.random.binomial(n=1,p=p,size=total))        
        contador+=1
    return estado



def dist_crimen(crimen=crimen,n=n,porcentaje=np.array([None]),min_porcent=min_porcent):
    
    if porcentaje.all() == None:
        vector_random=np.random.rand(crimen)
        vector_random/=sum(vector_random)
    else:
        vector_random=porcentaje
        
    while True in (vector_random < min_porcent):
        vector_random=np.random.rand(crimen)
        vector_random/=sum(vector_random)
    distribucion_crimen=[]
    for i in vector_random:
        distribucion_crimen.append(int(round(i*n)))
    while 0 in distribucion_crimen or sum(distribucion_crimen) != n:
        vector_random=np.random.rand(crimen)
        vector_random/=sum(vector_random)
        while True in (vector_random < min_porcent):
            vector_random=np.random.rand(crimen)
            vector_random/=sum(vector_random)
        distribucion_crimen=[]
        for i in vector_random:
            distribucion_crimen.append(int(round(i*n)))
    r=[]
    for j in range(len(distribucion_crimen)):
        for i in range(distribucion_crimen[j]):
            r+=[letras[j]]
    return r
        


def convert_vecinos_to_solution(vecinos):
    n=len(vecinos)
    M=[[0]*n for i in range(n)]
    solution=[]
    for i in range(n):
        for j in vecinos[i][2:]:
            M[i][j]=1
            
    for i in range(len(M)):
        solution+=M[i][i+1:]
    return solution
    

def generate(vertices,psi=psi,nu=nu,T=200,s=np.array([None]),lamda=lamda,modelo=modelo):
    n=len(vertices)
    
    #periodos en semanas
    #T=150 #6 aos
    if s.all() == None:
        s = np.random.rand(n)  # vector PoS de las personas en el intante t, al principio aleatorio
        
        
    #psi = 0.9  # velocidad perdida de memoria
    #nu = 0.85  # Impacto de la inseguridad
    
    St = np.zeros((T,n ))  # PoS a lo largo del tiempo
    #identificacion de cada sujeto con su respectiva media de crimen
    
    St[0] = s
    
    for t in range(1,T):
        
        # Al inicio de cada periodo aplicamos la perdida de memoria
        s = psi * s       
        ## crimen
        for k in range(n):
            # numero de crimenes sufridos por la persona k 
            X = np.random.poisson(lamda[vertices[k][1]])
            # posicion hubo crimen o no
            I = 0
            if X >= 1:  # si hubo al menos un crimen I=1 de lo contrario I=0
                I = 1
            # efecto del crimen en la percepcion de k para el siguiente periodo
            s[k] = I + (1 - I) * s[k] 

        #comunicacion 

        #copia
        scopia=s.copy()
        
        if modelo == "g_m_v":
        
            for k in range(n):
                vecinos = vertices[k][2:]
                media = 0
                for vecino in vecinos:
                    media+=scopia[vecino]
                media=media*1.0/len(vecinos)

                if scopia[k] > media:
                    s[k]=nu*scopia[k]+(1-nu)*media
                else:
                    s[k]=(1-nu)*scopia[k]+nu*media
                    
        elif modelo == "g_1_v":
            
            comu=np.random.permutation(n)[:int(n*0.1)]
            salto=[]
            
            for k in comu:
                
                if k in salto:
                    continue
                    
                if len(set(vertices[k][2:])-set(salto)) > 0:
                    
                    aux = np.random.choice(vertices[k][2:])

                    if scopia[k] > scopia[aux]:
                        s[k]=nu*scopia[k]+(1-nu)*scopia[aux]
                        s[aux]=nu*scopia[k]+(1-nu)*scopia[aux]
                    else:
                        s[k]=(1-nu)*scopia[k]+(nu)*scopia[aux]
                        s[aux]=(1-nu)*scopia[k]+(nu)*scopia[aux]
                        
                    salto.append(k)
                    salto.append(aux)
                    
        else:
            continue
            
            

        St[t] = s
        
        promedio=0
        for i in range(n):
            promedio+=np.mean(St.T[i][T/2:])
        promedio=promedio*1.0/n
        
    
    return St, promedio

def homofilia(vertices):
    edges={}
    for vertice in vertices:
        for vecino in vertice[2:]:
            if (vertice[0],vecino) in edges or (vecino,vertice[0]) in edges:
                pass
            else:
                edges[(vertice[0],vecino)]= 1*(vertice[1] == vertices[vecino][1])
    return sum(edges.values())*1.0/len(edges)


def draw_graph(G,fear,crime=3,labels=False):
    import networkx as nx
    
    s=1000*fear+100
    colors  = {"A":"green","B":"blue","C":"red","D":"orange","E":"purple","F":"pink","G":"yellow"}
    color=[]
    labels=[]
    for i in range(G.number_of_nodes()):
        color.append(colors[G.node[i]["crime"]])
    pos = nx.spring_layout(G)
    plt.figure(figsize=(30,20))
    nx.draw(G,pos=pos,with_labels=labels,node_size=s,node_color=color,alpha=0.5,font_color="w")
    
    
    from matplotlib.lines import Line2D

    legend_elements = [Line2D([0], [0], marker='o', color='w', label=key,
                              markerfacecolor=colors[key], markersize=40, alpha=0.5) for key in letras[:crime] ]

    # Create the figure
        
    plt.legend(handles=legend_elements, loc='best',fontsize=40)
    
    plt.show()
    
    
def assor(G):
    from networkx.algorithms.assortativity import attribute_assortativity_coefficient
    a=attribute_assortativity_coefficient(G=G,attribute='crime')
    return 0.5*a+0.5

def mixing_matrix(G):
    from networkx.algorithms.assortativity.mixing import attribute_mixing_matrix
    return attribute_mixing_matrix(G=G,attribute="crime")

def normpdf(x, mean, sd):
    import math
    var = float(sd)**2
    denom = (2*math.pi*var)**.5
    num = math.exp(-(float(x)-float(mean))**2/(2*var))
    return num/denom

def funcion_objetivo(state,s0,distribucion_crimen,n=n,tipo=tipo,lamda=lamda,psi=psi,nu=nu,modelo=modelo):
    
    v=convert_state_to_vecinos(n=n,state=state,dist_crimen=distribucion_crimen)
    S=generate(v,psi,nu,T=200,s=s0,lamda=lamda,modelo=modelo)[1]
    g=[]
    for node in v:
        g.append(len(node[2:]))                
    gmean=np.mean(g)
    
    gg=normpdf(gmean,5,0.5)+0.1
    
    
    h=homofilia(v)
    
    A=assor(convert_vertices_to_graph(v))
    
       
                 
                 
    if tipo == "shg":
        return (1-S)*(1-abs(h-0.6))*gg
    elif tipo == "sag":
        return (1-S)*(1-abs(A-0.8))*gg
    elif tipo == "sh":
        return (1-S)*(1-abs(h-0.6))
    elif tipo == "sg":
        return (1-S)*gg
    elif tipo == "sa":
        return (1-S)*(1-abs(A-0.8))
    else:
        return (1-S)
                 
                 

def inicializacion(individuos,n=n,crimen=crimen,min_porcent=min_porcent):
    Poblacion=[]
    for i in range(individuos):
        Poblacion.append(generate_estate(n=n))
    return Poblacion

def seleccion(Poblacion,s,distribucion_crimen,tipo=tipo,lamda=lamda,nu=nu,psi=psi,modelo=modelo):
    n=len(s)
    fdp=[]
    for i in range(len(Poblacion)):
        fdp.append(funcion_objetivo(n=n,state=Poblacion[i],s0=s,tipo=tipo,distribucion_crimen=distribucion_crimen,
                                    lamda=lamda,nu=nu,psi=psi,modelo=modelo))
    fdp=fdp+abs(min(fdp))+1
    fdp=fdp/sum(fdp)

    return fdp

def sample(Poblacion,fdp):
    P=[i for i in range(len(Poblacion))]
    return Poblacion[np.random.choice(P,p=fdp)]

def combinacion(state1,state2,n=n):
    total=n*(n-1)/2+1
    point_cross=np.random.randint(total)   
    
    h1=state1[:point_cross]+state2[point_cross:]
    h2=state2[:point_cross]+state1[point_cross:]
    
    while (validar_estado(h1,n=n) and validar_estado(h2,n=n)) == False:
        point_cross=np.random.randint(total)   
        h1=state1[:point_cross]+state2[point_cross:]
        h2=state2[:point_cross]+state1[point_cross:]
    
    
    return h1,h2

def mutacion(state,n=n,probabilidad=None):
    
    copia=copy.deepcopy(state)
    if not probabilidad:
        probabilidad=1.0/len(state)
        
    if np.random.binomial(1,probabilidad) == 1:
        rand1=np.random.randint(len(state))
        copia[rand1]=(copia[rand1]+1)%2
    
        while validar_estado(copia,n=n) == False:
            copia=copy.deepcopy(state)
            rand1=np.random.randint(len(state))
            copia[rand1]=(copia[rand1]+1)%2
            
        return copia
    
    else:
        return state
        
def plot(vertices,s,lamda=lamda,psi=psi,nu=nu,modelo=modelo,T=100):
    import seaborn as sn
    import matplotlib.pyplot as plt
    if len(lamda)== 3:
        colors={"A":"G","B":"B","C":"R"}
    else:
        colors  = {"A":"green","B":"blue","C":"red","D":"orange","E":"purple","F":"pink","G":"yellow"}
    S=generate(vertices,psi,nu,T,s,lamda,modelo)[0].T
    
    promedio=0
    for i in range(len(vertices)):
        promedio+=np.mean(S[i])
    promedio=promedio*1.0/len(vertices)
        
    
    
    G={}
    for vertice in vertices:
        if vertice[1] not in G:
            G[vertice[1]]=[]
        G[vertice[1]].append(vertice[0])
        
    l=[k for k in G.keys()]
    l.sort()

    
    for grupo in l:
        sn.tsplot(S[G[grupo]],color=colors[grupo],ci='sd')
        
    plt.legend(l)
    plt.xlabel("Time")
    plt.ylabel("Fear of crime")
    plt.show()
    return promedio

def grafica_grado_nodos(vecinos):
   
    grade={}
    for v in vecinos:
        g=len(v[2:])
        if g not in grade:
            grade[g]=1
        else:
            grade[g]+=1
    Y=np.array(grade.values())*1.0/sum(grade.values())
    X=grade.keys()
    plt.plot(np.log(X),np.log(Y))
    plt.title("Distribucion Grado Nodos (Log-Log)")
    plt.xlabel("Log(k)")
    plt.ylabel("Log(P(k))")
    plt.show()
    


from networkx.algorithms import approximation, assortativity,centrality, cluster, distance_measures, link_analysis, smallworld
from networkx.classes import function

def ver_medidas(G):
    print(function.info(G))
    """
    Numero minimo de nodos que deben ser removidos para desconectar G
    """
    print("Numero minimo de nodos que deben ser removidos para desconectar G :"+str(approximation.node_connectivity(G)))

    """
    average clustering coefficient of G.
    """
    print("average clustering coefficient of G: "+str(approximation.average_clustering(G)))

    """
    Densidad de un Grafo
    """
    print("Densidad de G: "+str(function.density(G)))

    """
    Assortativity measures the similarity of connections in
    the graph with respect to the node degree.
    Valores positivos de r indican que existe una correlacion entre nodos 
    con grado similar, mientras que un valor negativo indica
    correlaciones entre nodos de diferente grado
    """

    print("degree assortativity:"+str(assortativity.degree_assortativity_coefficient(G)))

    """
    Assortativity measures the similarity of connections
    in the graph with respect to the given attribute.
    """

    print("assortativity for node attributes: "+str(assortativity.attribute_assortativity_coefficient(G,"crime")))

    """
    Grado promedio vecindad
    """
    plt.plot(assortativity.average_neighbor_degree(G).values())
    plt.title("Grado promedio vecindad")
    plt.xlabel("Nodo")
    plt.ylabel("Grado")
    plt.show()

    """
    Grado de Centralidad de cada nodo
    """

    plt.plot(centrality.degree_centrality(G).values())
    plt.title("Grado de centralidad")
    plt.xlabel("Nodo")
    plt.ylabel("Centralidad")
    plt.show()


    """
    Calcular el coeficiente de agrupamiento para nodos
    """

    plt.plot(cluster.clustering(G).values())
    plt.title("coeficiente de agrupamiento")
    plt.xlabel("Nodo")
    plt.show()

    """
    Media coeficiente de Agrupamiento
    """
    print("Coeficiente de agrupamiento de G:"+str(cluster.average_clustering(G)))

    """
    Centro del grafo
    El centro de un grafo G es el subgrafo inducido por el 
    conjunto de vertices de excentricidad minima.

     La  excentricidad  de  v  in  V  se  define  como  la
     distancia maxima desde v a cualquier otro vertice del 
     grafo G siguiendo caminos de longitud minima.
    """

    print("Centro de G:"+ str(distance_measures.center(G)))

    """
    Diametro de un grafo
    The diameter is the maximum eccentricity.
    """
    print("Diametro de G:"+str(distance_measures.diameter(G)))


    """
    Excentricidad de cada Nodo
    The eccentricity of a node v is the maximum distance
    from v to all other nodes in G.
    """
    plt.plot(distance_measures.eccentricity(G).values())
    plt.title("Excentricidad de cada Nodo")
    plt.xlabel("Nodo")
    plt.show()

    """
    Periferia 
    The periphery is the set of nodes with eccentricity equal to the diameter.
    """
    print("Periferia de G:")
    print(distance_measures.periphery(G))

    """
    Radio
    The radius is the minimum eccentricity.

    """

    print("Radio de G:"+str(distance_measures.radius(G)))

    """
    PageRank calcula una clasificacion de los nodos
    en el grafico G en funcion de la estructura de 
    los enlaces entrantes. Originalmente fue disenado
    como un algoritmo para clasificar paginas web.
    """

    plt.plot(link_analysis.pagerank_alg.pagerank(G).values())
    plt.title("Puntaje de cada Nodo")
    plt.xlabel("Nodo")
    plt.show()

    """
    Coeficiente de Small World.
    A graph is commonly classified as small-world if sigma>1.

    """

    print("Coeficiente de Small World: " + str(smallworld.sigma(G)))

    """
    The small-world coefficient (omega) ranges between -1 and 1.
    Values close to 0 means the G features small-world characteristics.
    Values close to -1 means G has a lattice shape whereas values close
    to 1 means G is a random graph.
    """
    print("Omega coeficiente: "+str(smallworld.omega(G)))
    

def run(folder,total_generaciones,individuos,porcentaje_crimen,s0,n=n,crimen=crimen,tipo_objetivo=tipo,lamda=lamda,min_porcent=min_porcent,modelo=modelo):
    
    import sys, os, shutil
    import matplotlib as mpl
    mpl.use('Agg')
    
    if not os.path.exists(folder):
        os.mkdir(folder)
    
    archivo = open(os.path.join(folder,"solucion_"+str(tipo_objetivo)+"__"+str(modelo)+".txt"),'a')
    
    archivo.write("# nodos: "+ str(n)+ '\n')
    archivo.write("# grupos de crimen: "+ str(crimen)+ '\n')
    archivo.write("funcion objetivo: "+ str(tipo_objetivo)+ '\n')
    archivo.write("# de cromosomas por generacion: "+ str(individuos)+ '\n')
    archivo.write("minimo porcentaje de grupo: "+ str(min_porcent)+ '\n')
    archivo.write("Modelo utilizado: "+ str(modelo)+ '\n')
  
    archivo.write("-----------------------------------------------------------------"+'\n')

    distr_crimen=dist_crimen(crimen=crimen,n=n,
                          porcentaje=porcentaje_crimen,
                          min_porcent=min_porcent)
    
    Poblacion=inicializacion(individuos=individuos,
                         n=n,
                         crimen=crimen,
                         min_porcent=min_porcent)

    archivo.write("Media miedo inicial: "+ str(np.mean(s0))+ '\n')
    
    p_gen=[]
    
    for i in range(total_generaciones):
        archivo.write("-----------------------------------------------------------------------"+ '\n')
        archivo.write("Generacion "+ str(i)+ '\n')
        print("Generacion "+ str(i)+"/"+str(total_generaciones)+ '\n')

        puntaje_generacion=[]
        for estado in Poblacion:
            puntaje_generacion.append(funcion_objetivo(state=estado,
                                                       distribucion_crimen=distr_crimen,
                                                       s0=s0,
                                                       n=n,
                                                       tipo=tipo,
                                                       lamda=lamda,psi=psi,nu=nu,modelo=modelo))

        best_cromosome_generation=np.argsort(puntaje_generacion)[-1]

#         print("Mejor de la Generacion:")
#         print(Poblacion[best_cromosome_generation])

        media_crimen=plot(convert_state_to_vecinos(state=Poblacion[best_cromosome_generation],
                                                   dist_crimen=distr_crimen,n=n),
                          s0,lamda,psi,nu)

        archivo.write("Media de crimen:" + str(media_crimen)+ '\n')
        print("Media de crimen:" + str(media_crimen))
        homo=homofilia(convert_state_to_vecinos(state=Poblacion[best_cromosome_generation],
                                                   dist_crimen=distr_crimen,n=n))
        archivo.write("Homofilia: "+str(homo)+ '\n')
        print("Homofilia: "+str(homo))

        archivo.write("Puntaje Generacion "+str(np.mean(puntaje_generacion))+ '\n')
        print("Puntaje Generacion "+str(np.mean(puntaje_generacion)))
        p_gen.append(np.mean(puntaje_generacion))

        #funcion densidad de probabilidad para muestrear estados de la poblacion actual que depende de su desempeno
        fdp=seleccion(Poblacion=Poblacion,
                      s=s0,
                      distribucion_crimen=distr_crimen,
                      tipo=tipo,
                      lamda=lamda,
                      nu=nu,psi=psi,modelo=modelo)

        #Hijos de la poblacion actual
        Nueva_Generacion=[]
        # Combinacion 
        while len(Nueva_Generacion) != len(Poblacion):
            padre1=sample(Poblacion=Poblacion,fdp=fdp)
            padre2=sample(Poblacion=Poblacion,fdp=fdp)
            hijos=combinacion(state1=padre1,state2=padre2,n=n)
            contador=0
            while (validar_estado(estado=hijos[0],n=n) and validar_estado(estado=hijos[1],n=n)) == False:
                hijos=combinacion(state1=padre1,state2=padre2,n=n)
                if contador == 200:
                    hijos=[padre1,padre2]
                    break
                contador+=1
            Nueva_Generacion+=hijos

        # Mutacion
        for i in range(len(Nueva_Generacion)):
            Nueva_Generacion[i]=mutacion(Nueva_Generacion[i],n=n)

        # Reemplazo

        total = Poblacion+Nueva_Generacion

        fo=[]
        for t in total:
            fo.append(funcion_objetivo(state=t,
                                       distribucion_crimen=distr_crimen,
                                       s0=s0,
                                       n=n,
                                       tipo=tipo,
                                       lamda=lamda,psi=psi,nu=nu))
        order=np.argsort(fo)[::-1]
        best=order[:len(Poblacion)]
        for i in range(len(Poblacion)):
            Poblacion[i]=total[best[i]]
            
    archivo.write("////////////////////////////////////////////////////////////////"+ '\n')
    
    puntaje_generacion=[]
    for estado in Poblacion:
        puntaje_generacion.append(funcion_objetivo(state=estado,
                                                   distribucion_crimen=distr_crimen,
                                                   s0=s0,
                                                   n=n,
                                                   tipo=tipo,
                                                   lamda=lamda,psi=psi,nu=nu))

    best_cromosome_generation=np.argsort(puntaje_generacion)[-1]
    
    media_crimen=plot(convert_state_to_vecinos(state=Poblacion[best_cromosome_generation],
                                               dist_crimen=distr_crimen,n=n),
                      s0,lamda,psi,nu)
    
    print("Mejor Solucion:")
    archivo.write("Media de crimen:" + str(media_crimen)+ '\n')
    print("Media de crimen:" + str(media_crimen))
    
    homo=homofilia(convert_state_to_vecinos(state=Poblacion[best_cromosome_generation],
                                            dist_crimen=distr_crimen,n=n))
    
    archivo.write("Homofilia: "+str(homo)+ '\n')
    print("Homofilia: "+str(homo))

    archivo.close()

    np.save(os.path.join(folder,"solucion_"+str(tipo_objetivo)+"__"+str(modelo)),Poblacion[best_cromosome_generation])
    np.save(os.path.join(folder,"solucion_"+str(tipo_objetivo)+"__"+str(modelo)+"__"+"p_gen"),p_gen)
    
    
    
    return Poblacion[best_cromosome_generation], distr_crimen, p_gen


    