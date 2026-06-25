\[[Contents](./README.md)\]

# Multi arch ontainer registry setup for NSO dev

This document outlines the process used to setup a private
container registry for NSO development purposes.

## Save and publish Cisco provided images

### Receive NSO container images from Cisco rep

For the development environment we need both a `build` and `prod` image for all
NSO version expecting to be worked on. NSO container images are compile and
built for specific CPU architectures, if you want to develop on both x86 and
Apple silicon (arm64) be sure to acquire both versions for each type of
container, 4 total images for a single version of NSO.

### Load the Cisco NSO images locally

Images in `.signed.bin` format straight from the horse's mouth:

```
ls

-rw-r--r--@ 1 wbstephens  staff   666M Jul 26 14:32 nso-6.6.1.container-image-build.linux.arm64.signed.bin
-rw-r--r--@ 1 wbstephens  staff   758M Jul 26 14:33 nso-6.6.1.container-image-build.linux.x86_64.signed.bin
-rw-r--r--@ 1 wbstephens  staff   582M Jul 26 14:32 nso-6.6.1.container-image-prod.linux.arm64.signed.bin
-rw-r--r--@ 1 wbstephens  staff   668M Jul 26 14:33 nso-6.6.1.container-image-prod.linux.x86_64.signed.bin
```

Cisco create's these with a convenient self extracting script:

```
sh nso-6.6.1.container-image-build.linux.arm64.signed.bin
```

Output:

```
Unpacking...
Verifying files...
... [ output ommitted ]
```

The extracting script uses some crypto to check the validity of the downloaded
packages, do this 3 more times or for the remaining images.

#### Multi arch images in Docker

You should now have 4 `.tar.gz` files that can be loaded directly into local
Docker. We need hand these files on a per architecture basis due to Cisco using
overlapping generic names in there image files.

```
docker image load -i nso-6.6.1.container-image-build.linux.arm64.tar.gz
docker image load -i nso-6.6.1.container-image-prod.linux.arm64.tar.gz
```

Output:

```
fcd2d5769dc0: Loading layer [==================================================>]  260.8MB/260.8MB
85c9fbe78668: Loading layer [==================================================>]  1.486GB/1.486GB
Loaded image: cisco-nso-build:6.6.1
47daad53b1fe: Loading layer [==================================================>]  1.193GB/1.193GB
Loaded image: cisco-nso-prod:6.6.1
```

We need to re-tag these images based on the proper arch:

```
docker image tag cisco-nso-build:6.6.1 cisco-nso-build:6.6.1-arm64
docker image tag cisco-nso-prod:6.6.1 cisco-nso-prod:6.6.1-arm64
docker image rm cisco-nso-build:6.6.1
docker image rm cisco-nso-prod:6.6.1
```

Output:

```
Untagged: cisco-nso-build:6.6.1
Untagged: cisco-nso-prod:6.6.1
```

Proceed with the next arch:

```
docker image load -i nso-6.6.1.container-image-build.linux.x86_64.tar.gz
docker image load -i nso-6.6.1.container-image-prod.linux.x86_64.tar.gz
```

Re-jigger the tags:

```
docker image tag cisco-nso-build:6.6.1 cisco-nso-build:6.6.1-amd64
docker image tag cisco-nso-prod:6.6.1 cisco-nso-prod:6.6.1-amd64
docker image rm cisco-nso-build:6.6.1
docker image rm cisco-nso-prod:6.6.1
```

### Publish images on remote registry

We need to add remote registry details to all 4 tags:

```
docker image tag cisco-nso-build:6.6.1-arm64 container-registry.example.com/nso/cisco/cisco-nso-build:6.6.1-arm64
docker image tag cisco-nso-prod:6.6.1-arm64 container-registry.example.com/nso/cisco/cisco-nso-prod:6.6.1-arm64
docker image tag cisco-nso-build:6.6.1-amd64 container-registry.example.com/nso/cisco/cisco-nso-build:6.6.1-amd64
docker image tag cisco-nso-prod:6.6.1-amd64 container-registry.example.com/nso/cisco/cisco-nso-prod:6.6.1-amd64
```

With remote registry tag we can now publish the arch specific images to gitlab:

```
docker image push container-registry.example.com/nso/cisco/cisco-nso-build:6.6.1-arm64
docker image push container-registry.example.com/nso/cisco/cisco-nso-prod:6.6.1-arm64
docker image push container-registry.example.com/nso/cisco/cisco-nso-build:6.6.1-amd64
docker image push container-registry.example.com/nso/cisco/cisco-nso-prod:6.6.1-amd64
```

#### Multi arch images on remote registry

Next we create docker manifest which is magic that allows us to go back to a
generic image name that the local docker client can then select it's own proper
arch as needed.

\*\*Notes:

- all the arch specific images must be pushed to the remote registry prior
  to this step
- we only need to create remote registry manifest\*\*

```
docker manifest create container-registry.example.com/nso/cisco/cisco-nso-build:6.6.1 \
  container-registry.example.com/nso/cisco/cisco-nso-build:6.6.1-arm64 \
  container-registry.example.com/nso/cisco/cisco-nso-build:6.6.1-amd64
docker manifest create container-registry.example.com/nso/cisco/cisco-nso-prod:6.6.1 \
  container-registry.example.com/nso/cisco/cisco-nso-prod:6.6.1-arm64 \
  container-registry.example.com/nso/cisco/cisco-nso-prod:6.6.1-amd64
```

Output:

```
Created manifest list container-registry.example.com/nso/cisco/cisco-nso-build:6.6.1
Created manifest list container-registry.example.com/nso/cisco/cisco-nso-prod:6.6.1
```

Finally we can push the manifest to gitlab registry for availablility:

```
docker manifest push container-registry.example.com/nso/cisco/cisco-nso-build:6.6.1
docker manifest push container-registry.example.com/nso/cisco/cisco-nso-prod:6.6.1
```

______________________________________________________________________

\[[Top](#pyndev-package-configuration)\]\[[Contents](./README.md)\]
