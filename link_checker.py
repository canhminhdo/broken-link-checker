# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
import urllib.request
import colorama, re, queue, threading, time, sys
from colorama import Fore, Style
from urllib.parse import *

# Prod
# AUTH_BASIC = 'bWFzdGVyOm5ANHVyQGNAcjQ='
# BASE_URL = 'dev.naturacart.com'

# Dev
AUTH_BASIC = 'c3RhZ2luZzpuQDR1ckBjQHI0'
BASE_URL = 'stg.naturacart.com'
MAX_CONCURRENT_THREAD = 10
LOGGING = True

# CHECKER MODULE
def link_checker(source, address):
    try:
        req = urllib.request.Request(url=address)
        if address.find(BASE_URL) != -1:
            req.add_header("Authorization", "Basic %s" % AUTH_BASIC)
        resp = urllib.request.urlopen(req)
        if resp.status in [400, 404, 403, 408, 409, 501, 502, 503]:
            if LOGGING:
                print(Fore.RED + '[' + source +'] ' + resp.status + " " + resp.reason + "-->" + address + Style.RESET_ALL)
            ferror.write('[' + source +'] ' + resp.status + " " + resp.reason + "-->" + address + '\n')
        else:
            if LOGGING:
                print(Fore.GREEN + '[' + source +'] ' + "OK-->" + address + Style.RESET_ALL)
            fok.write('[' + source +'] ' + "OK-->" + address + '\n')
    except Exception as e:
        if LOGGING:
            print (Fore.RED + '[' + source +'] ' + "Exception-->{} {}".format(e,address) + Style.RESET_ALL)
        fexception.write('[' + source +'] ' + "Exception-->{} {}".format(e,address) + '\n')
        pass

# NORMALIZE URL
def normalize_url(a):
    try:
        if re.match('^#' ,a):
            return 0
        r = urlsplit(a)
        if r.scheme == '' and (r.netloc != '' or r.path != ''):
            d = urlunsplit(r)
            if re.match('^//' ,d):
                m = re.search('(?<=//)\S+', d)
                d = m.group(0)
                m = "https://"+d
                return m.rstrip('/')
            if re.match('^/{1}', d):
                return (website + a).rstrip('/')
        elif r.scheme == '' and r.netloc == '' and r.path != '':
            return website
        elif r.scheme == 'javascript' or r.scheme == 'mailto' or r.scheme == 'tel':
            if LOGGING:
                print(Fore.GREEN + "IGNORE-->" + a + Style.RESET_ALL)
        else:
            return a.rstrip('/')
    except Exception as e:
        pass

# EXTRACT MODULE
def link_extractor(address):
    fvisited.write(address + '\n')
    # tags = {'a':'href', 'img':'src', 'script':'src', 'link':'href'}
    try:
        req = urllib.request.Request(address)
        if address.find(BASE_URL) != -1:
            req.add_header("Authorization", "Basic %s" % AUTH_BASIC)

        res = urllib.request.urlopen(req)
        response = res.read().decode('utf-8')
        soup = BeautifulSoup(response, 'html.parser')

        # EXTRACT IMG
        for link in soup.find_all('img'):
            if link.has_attr('src'):
                p = normalize_url(link['src'])
                if p != 0 and str(p) != 'None':
                    link_checker(source=address, address=p)
        # ETRACT LINK CSS
        for link in soup.find_all('link'):
            if link.has_attr('href'):
                p = normalize_url(link['href'])
                if p != 0 and str(p) != 'None':
                    link_checker(source=address, address=p)
        # ETRACT LINK JS
        for link in soup.find_all('script'):
            if link.has_attr('src'):
                p = normalize_url(link['src'])
                if p != 0 and str(p) != 'None':
                    link_checker(source=address, address=p)
        # ETRACT LINK A
        for link in soup.find_all('a'):
            if link.has_attr('href'):
                p = normalize_url(link['href'])
                if p != 0 and str(p) != 'None':
                    link_checker(source=address, address=p)
                    threadLock.acquire()
                    if str(p).find(website) != -1 and p not in visitedLinks:
                        visitedLinks.add(p)
                        relativeLinks.put(p)
                    threadLock.release()
    except Exception as e:
        if LOGGING:
            print (Fore.RED + '[RELATIVE LINK] ' + "Exception-->{} {}".format(e,address) + Style.RESET_ALL)
        fexception.write('[RELATIVE LINK] ' + "Exception-->{} {}".format(e,address) + '\n')


def threader():
    while True:
        value = relativeLinks.get()
        if value is None:
            break
        link_extractor(value)
        relativeLinks.task_done()

if __name__=="__main__":
    # Init colorama
    colorama.init()

    # Open files to write
    fvisited = open('output/visited.txt', 'w', 1)
    ferror = open('output/error.txt', 'w')
    fexception = open('output/exception.txt', 'w')
    fok = open('output/ok.txt', 'w')

    # Init variables
    global website, relativeLinks, visitedLinks
    relativeLinks = queue.Queue()
    visitedLinks = set()

    website = input("Please enter the website address: ")
    # website = 'http://dev.naturacart.com''
    # website = 'https://stg.naturacart.com'
    visitedLinks.add(website.strip())
    threadLock = threading.Lock()
    threads = []

    # Start workers
    for x in range(MAX_CONCURRENT_THREAD):
        t = threading.Thread(target=threader)
        t.deamon = True
        t.start()
        threads.append(t)

    relativeLinks.put(website.strip())

    # Block until all tasks are done
    relativeLinks.join()

    # Stop workers
    for i in range(MAX_CONCURRENT_THREAD):
        relativeLinks.put(None)

    # Wait untill all thread completely
    for t in threads:
        t.join()

    # Close files
    fvisited.close()
    ferror.close()
    fexception.close()
    fok.close()

    # Exit
    sys.exit()