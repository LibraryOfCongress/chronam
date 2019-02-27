FROM openjdk:11 AS builder

RUN useradd --system -d /opt/solr -s /bin/false solr
RUN install -d -o solr -g solr /opt/solr /opt/solr/contrib /opt/solr/logs

USER solr

WORKDIR /tmp

RUN curl -LO https://archive.apache.org/dist/lucene/solr/4.10.4/solr-4.10.4.tgz
RUN tar -xf solr-4.10.4.tgz
RUN mv solr-4.10.4/example/* /opt/solr/

COPY conf/schema.xml /opt/solr/solr/collection1/conf/schema.xml
COPY conf/solrconfig.xml /opt/solr/solr/collection1/conf/solrconfig.xml

RUN curl --fail --silent --location --output /opt/solr/contrib/lucene-analyzers-stempel-4.10.4.jar https://repo1.maven.org/maven2/org/apache/lucene/lucene-analyzers-stempel/4.10.4/lucene-analyzers-stempel-4.10.4.jar
RUN curl --fail --silent --location --output /opt/solr/solr/collection1/conf/lang/stopwords_pl.txt https://raw.githubusercontent.com/apache/lucene-solr/master/lucene/analysis/stempel/src/resources/org/apache/lucene/analysis/pl/stopwords.txt

FROM openjdk:11

RUN useradd --system -d /opt/solr -s /bin/false solr
RUN install -d -o solr -g solr /opt/solr

# COPY ignores the USER directive so this MUST run as root before we
# chown & change to the less-privileged user:
COPY --from=builder /opt/solr/ /opt/solr/

RUN chown -R solr:solr /opt/solr
RUN install -d -o solr -g solr /opt/solr/logs /opt/solr/solr-webapp

USER solr

WORKDIR /opt/solr

EXPOSE 8983

ENTRYPOINT ["java", "-jar", "start.jar"]
