## Synopsis
Python API for Runtastic. 
Code used as baseline is https://github.com/timoschlueter/php-runtastic

## Code Example
TODO

## Motivation
Creating a python API 

## API Reference
####### Data Model
The following data model has been implemented in order to store required information:

- Dictionary __sessions
    - key:random_uuid (created within class)
      - value: dictionary
        - *key*: **username**           
            - *value*: **runtastic username**
        - *key*: **userid**             
            - *value*: **runtastic user id**
        - *key*: **authenticity_token** 
            - *value*: **runtastic authenticity token generated upon login**
        - *key*: **sport_sessions**     
            - *value*: **dictionary (containing json records for each session)**
                - *key*: **id**           
                   - *value*: **runtastic sport session id**

## Tests
TODO


## Installation
1. Download, 
2. In python-runtastic.ini adjust the [runtastic-user-settings] area where
    userName = <yourusername@email.com>
    userPassword = <yourpassword>

## License
The MIT License (MIT)

Copyright (c) 2016 giorger

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
