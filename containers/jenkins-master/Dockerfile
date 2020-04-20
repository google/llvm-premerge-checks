FROM jenkins/jenkins:lts

# disable CSRF protection, otherwise Phabricator can't trigger builds
ENV JENKINS_OPTS "-D hudson.security.csrf.GlobalCrumbIssuerConfiguration.DISABLE_CSRF_PROTECTION=true"