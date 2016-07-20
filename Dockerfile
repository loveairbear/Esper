FROM ubuntu:16.04
MAINTAINER Imran Ahmed

RUN apt-get update && apt-get install -y python3-pip \
                                         build-essential \
                                         wget
                          
#install cloud foundry cli for bluemix
RUN wget -O /tmp/cf-cli64.deb https://cli.run.pivotal.io/stable?release=debian64&version=6.20.0&source=github-rel
RUN dpkg -i /tmp/cf-cli64.deb



#add non-root user
RUN useradd -ms /bin/bash wizard

#set up password for root
RUN echo "root:kin" | chpasswd

#developement keys
ENV SLACK_API='placeholder'
ENV AMQP_URL='placeholder'
ENV MONGODB_URI='placeholder'
ENV ALCHEMY_API='placeholder' # optional
ENV SLACK_CLIENT='placeholder'
ENV SLACK_SECRET='placeholder'

# obfuscated url endpoints for auth,webhooks and more
ENV FB_ENDPOINT='placeholder'
ENV FB_TOKEN='placeholder'
ENV SLACK_ENDPOINT='placeholder'

