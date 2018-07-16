# Juju Charm(s) for deploying OpenMano

## Overview
These are the charm layers used to build Juju charms for deploying OpenVIM components. These charms are also published to the [Juju Charm Store](https://jujucharms.com/) and can be deployed directly from there using the [etsi-osm](https://jujucharms.com/u/nfv/osm-r1), or they can be build from these layers and deployed locally.

## Building the OpenVIM Charms

To build these charms, you will need [charm-tools][]. You should also read
over the developer [Getting Started][] page for an overview of charms and
building them. Then, in any of the charm layer directories, use `charm build`.
For example:

    (setup environment to build from layers)
    mkdir src
    cd src
    git clone https://github.com/nfvlabs/openvim.git
    export JUJU_REPOSITORY=$HOME/src/openvim/charms
    export INTERFACE_PATH=$JUJU_REPOSITORY/interfaces
    export LAYER_PATH=$JUJU_REPOSITORY/layers

    cd $LAYER_PATH/openvim
    charm build

    cd $LAYER_PATH/openvim-compute
    charm build

This will build the OpenVIM controller and OpenVIM compute charms, pulling in
 the appropriate base and interface layers from [interfaces.juju.solutions][], and place the resulting charms into $JUJU_REPOSITORY/builds.

You can also use the local version of a bundle:

    juju deploy openvim/charms/bundles/openmano.yaml

To publish:

    # You will need an account on Launchpad, and have it added to the ~nfv
    # namespace. Please contact foo@bar for these permissions.
    $ charm login

    $ cd $JUJU_REPOSITORY/builds/openvim

    # `charm push` will upload the charm into the store and report the revision
    # of the latest push.
    $ charm push . cs:~nfv/openvim
    blah blah cs:~nfv/openvim-4

    # Release the charm so that it is publicly consumable
    $ charm release cs:~nfv/openvim-4

    $ cd $JUJU_REPOSITORY/builds/openvim-compute

    # `charm push` will upload the charm into the store and report the revision
    # of the latest push.
    $ charm push . cs:~nfv/openvim-compute
    blah blah cs:~nfv/openvim-compute-4

    # Release the charm so that it is publicly consumable
    $ charm release cs:~nfv/openvim-compute-4

    # Finally, update and publish the bundle to point to the latest revision(s):

    cd $JUJU_REPOSITORY/bundles/openmano

    # Edit the `README.md` to reflect any notable changes.

    # Edit the `bundle.yaml` with the new revision to be deployed, i.e., change cs:~nfv/openvim-3 to cs:~nfv/openvim-4

    $ charm push . cs:~nfv/bundle/osm-r1
    blah blah cs:~nfv/bundle/osm-r1-4

    $ charm release cs:~nfv/bundle/osm-r1-4

To deploy the published charms from the charm store:

    # The recommended method
    $ charm deploy cs:~nfv/bundles/openmano

    - or -

    # The manual method
    $ juju deploy cs:~nfv/openvim
    $ juju deploy cs:~nfv/openvim-compute
    $ juju deploy cs:~nfv/openmano
    $ juju deploy cs:mariadb

    $ juju add-relation mariadb openvim
    $ juju add-relation mariadb openmano
    $ juju add-relation openvim openvim-compute
    $ juju add-relation openvim openmano

[charm-tools]: https://jujucharms.com/docs/stable/tools-charm-tools
[Getting Started]: https://jujucharms.com/docs/devel/developer-getting-started
[interfaces.juju.solutions]: http://interfaces.juju.solutions/
