# -*- coding: utf-8 -*-
"""
Created on Tue Nov 23 18:00:48 2021

@author: Lucas E. La Pietra
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import datetime
from urllib.parse import urlparse
from urllib.parse import parse_qs
import os
from git import Repo
import time
    
now = datetime.datetime.now()
years=range(2009,now.year+1)
months=range(1,13)
monthsOfThisYear=range(1,now.month+1)
urlbase='https://cdeluruguay.gob.ar/'
monthDict = {'Enero':1,'Febrero':2, 'Marzo':3, 'Abril':4,  
               'Mayo':5,  'Junio':6,  'Julio':7,  'Agosto':8,
               'Septiembre':9,  'Octubre':10,  'Noviembre':11,  'Diciembre':12}
contractsFolder=f'contratos/'
pathGit = './.git'  # make sure .git folder is properly configured
commitMessage = f'feat: update contracts {now}'
columnNames = ['Año','Mes','Rubro','CUIL proveedor','Razon social',
                   'Nombre Fantasia','Cantidad de contratados', 
                    'Importe']

def formatImportToNumber(text):
    text =text.replace(".","")
    text =text.replace(",",".")
    return text

def mapMarket(month, year, marketNumber, marketName):
    tableContent=[]
    page = requests.get(f'https://cdeluruguay.gob.ar/datagov/proveedoresContratadosAMRP.php?anio={year}&mes={month}&rubro={marketNumber}')
    content = page.text
    soup = BeautifulSoup(content,features="lxml")
    for row in soup.findAll('tr', attrs={'class':'textoTabla'}):
        rowElem=[]
        rowElem.append(year)
        rowElem.append(month)
        rowElem.append(marketName)
        for element in row.findAll('td'):
            text=element.text
            if '%' not in text:
                if ',' in text:
                    text = formatImportToNumber(text)
                rowElem.append(text)
        tableContent.append(rowElem) 
    df=pd.DataFrame(tableContent,columns=columnNames)
    return df 

def mapMonth(month,year):
    df=pd.DataFrame(columns=columnNames)
    page = requests.get(f'https://cdeluruguay.gob.ar/datagov/proveedoresContratadosAMR.php?anio={year}&mes={month}')
    content = page.text
    soup = BeautifulSoup(content,features="lxml")
    for row in soup.findAll('tr', attrs={'class':'textoTabla'}):
        marketName=row.find('td',attrs={'align':'left'}).text
        url=urlbase+row.find('a')['href']
        parsedUrl = urlparse(url)
        marketNumber = parse_qs(parsedUrl.query)['rubro'][0]
        df=df.append(mapMarket(month, year, marketNumber, marketName), ignore_index=True)
    if not df.empty:       
        route=f'{contractsFolder}contratos-{month}-{year}.xlsx'
        df.to_excel(route, index = False)
        print(f'month {month} of year {year} mapped successfully')
    else:
        print(f'month {month} of year {year} does not have any contract yet')

def mapYear(year):
    if year==now.year:
       for month in monthsOfThisYear:
           if not os.path.exists(f'./{contractsFolder}contratos-{month}-{year}.xlsx'):
               mapMonth(month,year)
    else:
       for month in months:
           if not os.path.exists(f'./{contractsFolder}contratos-{month}-{year}.xlsx'):
               mapMonth(month,year)
    print(f'year {year} mapped successfully')

def writeLastRun():
    page = requests.get(f'https://cdeluruguay.gob.ar/datagov/proveedoresContratados.php')
    content = page.text
    soup = BeautifulSoup(content,features="lxml")
    dateCell=soup.find('td', text='Fecha última actualización')
    row=dateCell.find_parent('tr')
    date=row.find('td', attrs={'class':'textoTablaReporte'}).text
    file = open("lastRunDate.txt", "w")
    file.write(date)
    file.close()
    print('last run wrote successfully')

def checkLastUpdate():
    page = requests.get(f'https://cdeluruguay.gob.ar/datagov/proveedoresContratados.php')
    content = page.text
    soup = BeautifulSoup(content,features="lxml")
    dateCell=soup.find('td', text='Fecha última actualización')
    row=dateCell.find_parent('tr')
    date=row.find('td', attrs={'class':'textoTablaReporte'}).text
    return date  

def isScrapingUpToDate():
    if os.path.exists('./lastRunDate.txt'):
        lastUpdate=checkLastUpdate()
        with open('lastRunDate.txt') as file:
            lastRunDate = file.read()
            if lastRunDate==lastUpdate:
                return True
            else:
                return False
    else:
        return False
        
def appendAllYears():
    df=pd.DataFrame(columns=columnNames)
    for year in years:
        for month in months:
            if os.path.exists(f'./{contractsFolder}contratos-{month}-{year}.xlsx'):
                df=df.append(pd.read_excel(f'{contractsFolder}contratos-{month}-{year}.xlsx'))   
    route=f'{contractsFolder}contratos-complete.csv'
    df.to_csv(route, index = False)   
    
def mapComplete():
    for year in years:
        if year != now.year:
            if not os.path.exists(f'./{contractsFolder}contratos-{12}-{year}.xlsx'):
                mapYear(year)
        else:
            if not isScrapingUpToDate() or not os.path.exists(f'./{contractsFolder}contratos-{now.month}-{year}.xlsx'):
                mapYear(year) 
                appendAllYears() 
                writeLastRun()
                time.sleep(5)
                git_push()
            else:
                print('Contracts are up to date')
    
def git_push():
    try:
        repo = Repo(pathGit)
        repo.git.add(update=True)
        repo.index.commit(commitMessage)
        origin = repo.remote(name='origin')
        origin.push()
        print('New contracts pushed successfully')   
    except:
        print('An error occured while pushing the code')      


if not os.path.exists(f'./{contractsFolder}'):
            os.mkdir(contractsFolder)
mapComplete()  
 


