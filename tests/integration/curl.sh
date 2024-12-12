CODEARTIFACT_AUTH_TOKEN=$(aws codeartifact get-authorization-token --domain codeartifact-backup-domain --domain-owner $ACCOUNT --query authorizationToken --output text) 


curl --request PUT "https://codeartifact-backup-domain-$ACCOUNT.d.codeartifact.$REGION.amazonaws.com/maven/codeartifact-backup-repository/com/amazonaws/app/internal-library/1.0/internal-library-1.0.jar" \
     --user "aws:$CODEARTIFACT_AUTH_TOKEN" --header "Content-Type: application/octet-stream" \
     --data-binary @assets/internal-library-1.0.jar

curl --request PUT "https://codeartifact-backup-domain-$ACCOUNT.d.codeartifact.$REGION.amazonaws.com/maven/codeartifact-backup-repository/com/amazonaws/app/internal-library/maven-metadata.xml" \
     --user "aws:$CODEARTIFACT_AUTH_TOKEN" --header "Content-Type: application/octet-stream" \
     --data-binary @assets/maven-metadata.xml



