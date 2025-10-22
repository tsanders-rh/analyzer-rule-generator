# Migration Guide Index

A curated list of migration guides for testing the analyzer rule generator.

## Java / Jakarta EE

### Spring Boot
- **Spring Boot 3.0**: https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-3.0-Migration-Guide
- **Spring Boot 4.0**: https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-4.0-Migration-Guide

### Quarkus
- **Quarkus REST (RESTEasy Reactive)**: https://quarkus.io/guides/resteasy-reactive-migration
- **OpenTracing to OpenTelemetry**: https://quarkus.io/guides/opentelemetry-tracing
- **Vert.x OIDC to Quarkus OIDC**: https://quarkus.io/guides/security-oidc-bearer-token-authentication-tutorial

### Jakarta EE
- **Jakarta EE 9 (javax → jakarta)**: https://jakarta.ee/learn/docs/jakartaee-tutorial/
- **Jakarta EE 10**: https://jakarta.ee/specifications/platform/10/

## JavaScript / TypeScript

### React
- **React 18**: https://react.dev/blog/2022/03/08/react-18-upgrade-guide
- **React 19**: https://react.dev/blog/2024/04/25/react-19-upgrade-guide

### PatternFly
- **PatternFly v5 → v6**: https://www.patternfly.org/get-started/upgrade/

### Angular
- **Angular Update Guide**: https://update.angular.io/

### Vue
- **Vue 2 → Vue 3**: https://v3-migration.vuejs.org/

## Python

### Python Core
- **Python 3.13 What's New**: https://docs.pythondocs.org/en/3.13/whatsnew/3.13.html
- **Python 3.12 What's New**: https://docs.python.org/3/whatsnew/3.12.html
- **Python 2 to 3**: https://docs.python.org/3/howto/pyporting.html

### Django
- **Django 4.2 → 5.0**: https://docs.djangoproject.com/en/5.0/howto/upgrade-version/
- **Django 5.0 → 5.1**: https://docs.djangoproject.com/en/5.1/howto/upgrade-version/
- **Django 4.0 → 4.1**: https://docs.djangoproject.com/en/4.1/howto/upgrade-version/
- **Django 4.1 → 4.2**: https://docs.djangoproject.com/en/4.2/howto/upgrade-version/

### FastAPI
- **Pydantic v1 → v2**: https://fastapi.tiangolo.com/release-notes/#01190
- **FastAPI Migration Guide**: https://fastapi.tiangolo.com/migration/

### Flask
- **Flask 2.x → 3.x**: https://flask.palletsprojects.com/en/stable/changes/

## Cloud / Infrastructure

### Azure
- **Azure Functions Flex Consumption**: https://github.com/erwinkramer/azure-functions-flex-consumption-migration-guide

### Kubernetes
- **Deprecated API Migration**: https://kubernetes.io/docs/reference/using-api/deprecation-guide/

## Testing Status

| Guide | Status | Rules Generated | Notes |
|-------|--------|-----------------|-------|
| Spring Boot 4.0 | ✅ Tested | 18 | MongoDB config, deprecated APIs |
| React 19 | ✅ Tested | 4 | API updates, test utils |
| PatternFly v5→v6 | ✅ Tested | 15 | React component changes |
| Quarkus REST | 🔲 Not tested | - | |
| React 18 | 🔲 Not tested | - | |
| Jakarta EE 9 | 🔲 Not tested | - | Namespace migration |
| Angular | 🔲 Not tested | - | |
| Django | 🔲 Not tested | - | |

## Contributing

When adding new migration guides:
1. Test with the rule generator
2. Note the number of rules generated
3. Document any issues or special handling needed
4. Update the testing status table
