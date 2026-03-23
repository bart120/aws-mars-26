$Key = "C:\temp\ec2-kp-vl.pem"

icacls $Key /inheritance:r
icacls $Key /remove "AUTORITE NT\Utilisateurs authentifiés"
icacls $Key /remove "BUILTIN\Utilisateurs"
icacls $Key /remove "BUILTIN\Administrateurs"
icacls $Key /remove "AUTORITE NT\Système"
icacls $Key /grant:r "$($env:USERNAME):(R)"