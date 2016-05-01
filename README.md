### Getting Started
this app requires a few environment variables like:
SLACK_API 
AMQP_URL 
ALCHEMY_API 
MONGODB_URI

1. install dependencies:
    '''
    pip install -r requirements.txt
    '''
2. start! :
    '''
    bash start.sh 
    '''


### Vendoring app dependencies
As stated in the [Disconnected Environments documentation](https://github.com/cf-buildpacks/buildpack-packager/blob/master/doc/disconnected_environments.md), your application must 'vendor' it's dependencies.

For the Python buildpack, use ```pip```:

```shell 
cd <your app dir>
mkdir -p vendor

# vendors all the pip *.tar.gz into vendor/
pip install --download vendor -r requirements.txt
```

```cf push``` uploads your vendored dependencies. The buildpack will install them directly from the `vendor/`.
