/*
 * Copyright (c) 2015 SONATA-NFV
 * ALL RIGHTS RESERVED.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * Neither the name of the SONATA-NFV
 * nor the names of its contributors may be used to endorse or promote
 * products derived from this software without specific prior written
 * permission.
 *
 * This work has been performed in the framework of the SONATA project,
 * funded by the European Commission under Grant number 671517 through
 * the Horizon 2020 and 5G-PPP programmes. The authors would like to
 * acknowledge the contributions of their colleagues of the SONATA
 * partner consortium (www.sonata-nfv.eu).
 */

/* Simple javascript to create MongoDB databases for son-catalogue
 * This scripts needs to be run with 'installation_mongodb.sh' script
 * for a fresh MongoDB install. However, it can be run as standalone
 * with the next command from prompt if mongo is already installed:
 * sudo mongo --nodb create_db.js
 *
 * If the MongoDB is not found in localhost or is located on a different
 * port, then change "localhost:27017" accordingly from each 'connect'
 * command to the "ip_address:port" where MongoDB is installed/located.
 * Mongo Shell is required on local machine to apply script on remote a
 * remote database.
 */

db = connect("mongo:27017/son-catalogue-repository");
db.createCollection("nsd");
db.createCollection("vnfd");
db.createCollection("pd");

/* Uncomment next lines if MongoDB installation will be done in localhost, and comment lines above */
//db = connect("127.0.0.1:27017/son-catalogue-repository");
//db.createCollection("nsd");
//db.createCollection("vnfd");
//db.createCollection("pd");

