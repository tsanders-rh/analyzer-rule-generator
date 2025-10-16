// Application.java
package com.example;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.stereotype.Component;
import org.springframework.boot.test.mock.mockito.MockitoTestExecutionListener;

@SpringBootApplication
@EnableConfigurationProperties(MongoProperties.class)
public class Application {

    public static void main(String[] args) {
        SpringApplication.run(Application.class, args);
    }

    // Rule spring-boot-3.5-to-spring-boot-4.0-00001
    @Value("${spring.data.mongodb.additional-hosts}")
    private String[] additionalHosts;

    // Rule spring-boot-3.5-to-spring-boot-4.0-00002
    @Value("${spring.data.mongodb.authentication-database}")
    private String authenticationDatabase;

    // Rule spring-boot-3.5-to-spring-boot-4.0-00003
    @Value("${spring.data.mongodb.database}")
    private String database;

    // Rule spring-boot-3.5-to-spring-boot-4.0-00004
    @Value("${spring.data.mongodb.host}")
    private String host;

    // Rule spring-boot-3.5-to-spring-boot-4.0-00005
    @Value("${spring.data.mongodb.password}")
    private String password;

    // Rule spring-boot-3.5-to-spring-boot-4.0-00006
    @Value("${spring.data.mongodb.port}")
    private int port;

    // Rule spring-boot-3.5-to-spring-boot-4.0-00007
    @Value("${spring.data.mongodb.protocol}")
    private String protocol;

    // Rule spring-boot-3.5-to-spring-boot-4.0-00008
    @Value("${spring.data.mongodb.replica-set-name}")
    private String replicaSetName;

    // Rule spring-boot-3.5-to-spring-boot-4.0-00009
    @Value("${spring.data.mongodb.representation.uuid}")
    private String representationUuid;

    // Rule spring-boot-3.5-to-spring-boot-4.0-00010
    @Value("${spring.data.mongodb.ssl.bundle}")
    private String sslBundle;

    // Rule spring-boot-3.5-to-spring-boot-4.0-00011
    @Value("${spring.data.mongodb.ssl.enabled}")
    private boolean sslEnabled;

    // Rule spring-boot-3.5-to-spring-boot-4.0-00012
    @Value("${spring.data.mongodb.uri}")
    private String uri;

    // Rule spring-boot-3.5-to-spring-boot-4.0-00013
    @Value("${spring.data.mongodb.username}")
    private String username;

    // Rule spring-boot-3.5-to-spring-boot-4.0-00014
    @Value("${management.health.mongo.enabled}")
    private boolean mongoHealthEnabled;

    // Rule spring-boot-3.5-to-spring-boot-4.0-00015
    @Value("${management.metrics.mongo.command.enabled}")
    private boolean mongoCommandMetricsEnabled;

    // Rule spring-boot-3.5-to-spring-boot-4.0-00016
    @Value("${management.metrics.mongo.connectionpool.enabled}")
    private boolean mongoConnectionPoolMetricsEnabled;

    // Rule spring-boot-3.5-to-spring-boot-4.0-00017
    @Bean
    public MockitoTestExecutionListener mockitoTestExecutionListener() {
        return new MockitoTestExecutionListener();
    }
}

@Component
@ConfigurationProperties(prefix = "spring.data.mongodb")
class MongoProperties {
    // Additional properties to ensure ConfigurationProperties is used
    private String database;
    private String host;
    private String username;
    private String password;

    public String getDatabase() {
        return database;
    }

    public void setDatabase(String database) {
        this.database = database;
    }

    public String getHost() {
        return host;
    }

    public void setHost(String host) {
        this.host = host;
    }

    public String getUsername() {
        return username;
    }

    public void setUsername(String username) {
        this.username = username;
    }

    public String getPassword() {
        return password;
    }

    public void setPassword(String password) {
        this.password = password;
    }
}