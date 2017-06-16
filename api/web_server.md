# Web Server Interfaces

## LoginHandler

- get
    - return: login page html

- post
    - params
        username:
        password:
    - return



## SearchHandler

- get
    - return: result page html if logined, otherwise redirect to login page.

- post
    - params:
        domain: target name
        brute: true or false
        https: true or false
        search_engine: true or false
        page_catche: true or false
        recursive_page_catche: true or false
    - return: result page html with some data

    Datas will be displayed in the page while the users had searched it.


## ResultHandler:

- get:
    - params:
        type: 0 -> sub domains and ip, 1 -> whois, 2 -> http_header
        domain: target domain
    - return:
        sub domains:
            {
                sub: ip,
                ...
            }
        whois
            {

            }
        http_header:
            {

            }


## LogoutHandler:


## HistoryHandler:
