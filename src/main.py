from bs4 import BeautifulSoup
import urllib.request
from tkinter import *
from tkinter import messagebox
import re, os, shutil
from datetime import datetime
from whoosh import qparser, query
from whoosh.index import create_in, open_dir
from whoosh.fields import Schema, TEXT, DATETIME, NUMERIC, KEYWORD, ID  # Agregado NUMERIC
from whoosh.qparser import QueryParser, MultifieldParser, OrGroup

# lineas para evitar error SSL
import ssl
if (not os.environ.get('PYTHONHTTPSVERIFY', '') and
getattr(ssl, '_create_unverified_context', None)):
    ssl._create_default_https_context = ssl._create_unverified_context

url="https://www.recetasgratis.net/Recetas-de-Aperitivos-tapas-listado_receta-1_1.html"
def cargar():
    respuesta = messagebox.askyesno(title="Confirmar",message="Esta seguro que quiere recargar los datos. \nEsta operación puede ser lenta")
    if respuesta:
        almacenar_datos()


def almacenar_datos():
    
    schem = Schema(
        titulo=TEXT(stored=True, phrase=False),
        numero_Comensales=NUMERIC(stored=True, numtype=int),
        autor=TEXT(stored=True,phrase=True),
        fecha=DATETIME(stored=True),
        caracteristicas=KEYWORD(stored=True,commas=True,lowercase=True),
        introduccion=TEXT(stored=True,phrase=False)
    )    
    if os.path.exists("Index"):
        shutil.rmtree("Index")
    os.mkdir("Index")
    

    ix = create_in("Index", schema=schem)
    writer = ix.writer()
    i=0
    lista=extraer_recetas(url)
    for pelicula in lista:
        writer.add_document(titulo=str(pelicula[0]), numero_Comensales=int(pelicula[1]), autor=str(pelicula[2]), fecha=pelicula[3], caracteristicas=str(pelicula[4]), introduccion=str(pelicula[5]))  
        i+=1
    writer.commit()
    messagebox.showinfo("Fin de indexado", "Se han indexado "+str(i)+ " recetas")          

    
def extraer_recetas(url):
    import locale
    locale.setlocale(locale.LC_TIME, "es_ES")
    
    lista=[]
    f = urllib.request.urlopen(url)
    s = BeautifulSoup(f,"lxml")
    l= s.find_all("div", class_=['resultado','link'])
    for i in l:
        titulo = i.a.string.strip()
        comensales = i.find("span",class_="comensales")
        if comensales:
            comensales = int(comensales.string.strip())
        else:
            comensales=-1
        
        f1 = urllib.request.urlopen(i.find('a')['href'])
        s1 = BeautifulSoup(f1,"lxml")
        autor = s1.find("div", class_='nombre_autor').a.string.strip()
        fecha = s1.find("div", class_='nombre_autor').find('span', class_="date_publish").string
        fecha = fecha.replace('Actualizado:','').strip()
        fecha = datetime.strptime(fecha, "%d %B %Y")
        introduccion = s1.find("div", class_="intro").text
        caracteristicas = s1.find("div", class_="properties inline")
        if caracteristicas:
            caracteristicas = caracteristicas.text.replace("Características adicionales:","")
            caracteristicas = ",".join([c.strip() for c in caracteristicas.split(",")] )     
        else:
            caracteristicas = "sin definir"
        lista.append((titulo, comensales, autor, fecha, caracteristicas,introduccion))
    
    return lista


def listar(list):
    v=Toplevel()
    sc=Scrollbar(v)
    sc.pack(side=RIGHT,fill=Y)
    lb=Listbox(v,width=150,yscrollcommand=sc.set)
    for row in list:
        lb.insert(END,"\n")
        s=row['titulo'].upper()
        lb.insert(END,s)
        s="Numero de Comensales: " + str(row['numero_Comensales'])
        lb.insert(END,s)
        s="Autor: "+row['autor']
        lb.insert(END,s)
        s="Fecha de actutualizacion: "+parseFecha(row['fecha'])
        lb.insert(END,s)
        s="Caracteristicas: "+row['caracteristicas']
        lb.insert(END,s)
    lb.pack(side=LEFT, fill=BOTH)
    sc.config(command=lb.yview)

def tituloIntroduccion():
    def listar_titulo_introduccion(event):
        ix=open_dir("Index")
        with ix.searcher() as searcher:
            myquery = MultifieldParser(["titulo","introduccion"], ix.schema).parse(str(entry.get()))
            results= searcher.search(myquery)
            listar(results)
    v=Toplevel()
    label=Label(v,text="Introduzca la palabra a buscar: ")
    label.pack(side=LEFT)
    entry=Entry(v)
    entry.bind("<Return>", listar_titulo_introduccion)
    entry.pack(side=LEFT)
    

def parseFecha(date):
    return str(date).replace("00:00:00"," ")

def ventana_principal():
    def listar_todo():
        ix=open_dir("Index")
        with ix.searcher() as searcher:
            results = searcher.search(query.Every(),limit=None)
            print(len(results))
            listar(results) 
    
    root = Tk()
    menubar = Menu(root)
    
    datosmenu = Menu(menubar, tearoff=0)
    datosmenu.add_command(label="Cargar", command=cargar)
    datosmenu.add_separator()   
    datosmenu.add_command(label="Listar", command=listar_todo)
    datosmenu.add_separator()   
    datosmenu.add_command(label="Salir", command=root.quit)
    
    menubar.add_cascade(label="Datos", menu=datosmenu)
    
    buscarmenu = Menu(menubar, tearoff=0)
    buscarmenu.add_command(label="Título o Introducción", command=tituloIntroduccion)
    buscarmenu.add_command(label="Fecha", command=root.quit)
    buscarmenu.add_command(label="Caracteristicas y Titulo", command=root.quit)
    
    menubar.add_cascade(label="Buscar", menu=buscarmenu)
        
    root.config(menu=menubar)
    root.mainloop()

    

if __name__ == "__main__":
    ventana_principal()