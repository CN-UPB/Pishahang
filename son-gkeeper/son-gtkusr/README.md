# [SONATA](http://www.sonata-nfv.eu)'s Gatekeeper User Management micro-service
[![Build Status](http://jenkins.sonata-nfv.eu/buildStatus/icon?job=son-gkeeper)](http://jenkins.sonata-nfv.eu/job/son-gkeeper)

This is the folder of the **User Management** micro-service. This micro-service is used by the [`Gatekeeper API`](https://github.com/sonata-nfv/son-gkeeper/son-gtkapi) and is currently under development.

## User Management

This micro-service enables identity, authentication and authorization features to the **Service Platform**, including features such:

- **Control** for who can access to the Service Platform and what can be accessed
- Users and Micro-services **Authentication and Authorization**
- Manages **User Accounts** for different types of users
- Manages **Service Accounts**; Micro-services are a different entity where no user is behind
- Enables support for **Direct Access Grants**, exchanging user credentials to obtain an access token (JWT)
- Supports two User type roles: **developer** and **customer**
- Supports Micro-services roles
- Supports Users **groups**
- Supports **users' public key** storage for signing features (requires MongoDB database)

## Building
The User Management micro-service is part of the Gatekeeper, and it can't be built as a standalone component.
Given this approach, it is required to be built along with the available Gatekeeper micro-services. So:

* each micro-service is provided in its own container (we're using [`docker`](https://github.com/docker/docker));
* the `Dockerfile` in each folder specifies the environment the container needs to work;
* the `docker-compose.yml` file in the root of this repository provides the linking of all the micro-services.

Furthermore, the User Management module **requires** the Keycloak Identity and Access Management server.
The [`son-keycloak`](https://github.com/sonata-nfv/son-gkeeper/son-keycloak) component includes all the required configuration and deployment settings.

### Dependencies
The libraries the Gatekeep depends on are the following:

* [`ci_reporter`](https://github.com/ci-reporter/ci_reporter) >=2.0.0 (MIT)
* [`ci_reporter_rspec`](https://github.com/ci-reporter/ci_reporter_rspec) >=1.0.0 (MIT)
* [`curb`](https://github.com/taf2/curb) >=0.9.3 (MIT)
* [`jwt`](https://github.com/jwt/ruby-jwt) >=1.5.5 (MIT)
* [`mongoid`](https://github.com/mongodb/mongoid) >=4.0 (MIT)
* [`mongoid-pagination`](https://github.com/ajsharp/mongoid-pagination) >=0.2 (MIT)
* [`puma`](https://github.com/puma/puma) >=3.4.0 (BSD-3-CLAUSE)
* [`rake`](https://github.com/ruby/rake) >=11.2.2 (MIT)
* [`rest-client`](https://github.com/rest-client/rest-client) >=2.0.0 (Apache 2.0)
* [`ruby`](https://github.com/ruby/ruby/tree/ruby_2_2) >=2.2.0 (MIT)
* [`sinatra`](https://github.com/sinatra/sinatra) >=1.4.7 (MIT)
* [`sinatra-contrib`](https://github.com/sinatra/sinatra-contrib) >=1.4.7 (MIT)

For the micro-services implemented in [ruby](http://www.ruby-lang.org) these dependencies can be checked in each folder's `Gemfile`.

### Contributing
Contributing to the Gatekeeper User Management is really easy. You must:

1. Clone [this repository](http://github.com/sonata-nfv/son-gkeeper);
1. Work on your proposed changes, preferably through submiting [issues](https://github.com/sonata-nfv/son-gkeeper/issues);
1. Submit a Pull Request;
1. Follow/answer related [issues](https://github.com/sonata-nfv/son-gkeeper/issues) (see Feedback-Chanel, below).

## Installation
Installing the Gatekeeper User Management is really easy. You'll need:

1. the [ruby](http://www.ruby-lang.org) programming language: we prefer doing this by using a version manager tool such as [rvm](https://rvm.io) or [rbenv](http://rbenv.org) (we are using version **2.2.3**);
1. in each one of the subfolders, just run:
  1. `bundle install`
  1. please follow each specific folder's instructions on which environment variables to set
  1. `rake start`

## Usage
Please refer to the [`son-gtkapi`](https://github.com/sonata-nfv/son-gkeeper/tree/master/son-gtkapi) repository and each one of the other folders in this repository for examples of usage of each one of the already developed micro-services.

## Documentation
Please refer to the [`Gatekeeper Github Wiki`](https://github.com/sonata-nfv/son-gkeeper/wiki) sections and check for User Management pages, which include information and examples of usage of its features.

## License
The license of the SONATA Gatekeeper is Apache 2.0 (please see the [license](https://github.com/sonata-nfv/son-editorgkeeper/blob/master/LICENSE) file).

---
#### Lead Developers

The following lead developers are responsible for this micro-service and have admin rights. They can, for example, merge pull requests.

* Daniel Guija ([dang03](https://github.com/dang03))

#### Feedback-Chanels

Please use the [GitHub issues](https://github.com/sonata-nfv/son-gkeeper/issues) and the SONATA development mailing list `sonata-dev@lists.atosresearch.eu` for feedback.

