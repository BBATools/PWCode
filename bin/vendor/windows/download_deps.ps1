function Get-RedirectedUrl
{
    Param (
        [Parameter(Mandatory=$true)]
        [String]$URL
    )

    $request = [System.Net.WebRequest]::Create($url)
    $request.AllowAutoRedirect=$false
    $response=$request.GetResponse()

    If ($response.StatusCode -eq "Found")
    {
        $response.GetResponseHeader("Location")
    }
}

[Net.ServicePointManager]::SecurityProtocol = "tls12, tls11, tls"
$binPath = (get-item $PSScriptRoot).FullName
$pythonPath = [IO.Path]::Combine($binPath, 'python')
$jrePath = [IO.Path]::Combine($binPath, 'jre')

# Download SQL Workbench J
# $wbTestPath = [IO.Path]::Combine($binPath, 'sqlworkbench.jar')
# If (-Not (Test-Path $wbTestPath)) {
# 	$url= "https://www.sql-workbench.eu/Workbench-Build125.zip"
# 	$filename = [System.IO.Path]::GetFileName($url); 
# 	Write-Host "Downloading $filename (approx. 6MB)"
# 	Invoke-WebRequest -Uri $url -OutFile $filename
# 	Write-Host "Extracting $filename  to $binPath"
# 	Expand-Archive $filename -DestinationPath $binPath
# }

# Download Python
# $pythonTestPath = [IO.Path]::Combine($pythonPath, 'python3.exe')
# If (-Not (Test-Path $pythonTestPath)) {
# 	$url= "https://www.python.org/ftp/python/3.6.8/python-3.6.8-embed-amd64.zip"
# 	New-Item -ItemType Directory -Force -Path $pythonPath 
#     $filename = [System.IO.Path]::GetFileName($url); 
#     Write-Host "Downloading $filename (approx. 7MB)"
#     Invoke-WebRequest -Uri $url -OutFile $filename
#     Write-Host "Extracting $filename  to $binPath"
#     Expand-Archive $filename -DestinationPath $pythonPath
#     #Fix python path
#     $pthFile = [IO.Path]::Combine($pythonPath, 'python36._pth')
#     $text = [string]::Join("`n", (Get-Content $pthFile))
# 	[regex]::Replace($text, "\.`n", ".`n..\PWB`n", "Singleline") | Set-Content $pthFile
# }

# Download wimlib
# $wimlibTestPath = [IO.Path]::Combine($binPath, 'PWB','wimlib-imagex.exe')
# If (-Not (Test-Path $wimlibTestPath)) {
#     $url= "https://wimlib.net/downloads/wimlib-1.13.1-windows-x86_64-bin.zip"
#     $filename = [System.IO.Path]::GetFileName($url); 
#     Write-Host "Downloading $filename (approx. 1MB)"
#     Invoke-WebRequest -Uri $url -OutFile $filename
#     Write-Host "Extracting $filename  to $binPath"
#     Expand-Archive $filename -DestinationPath $PSScriptRoot
# }

# cd amazon-corretto-*-linux-x64/bin/
# ./jlink --output $SCRIPTPATH/vendor/linux/jre --compress=2 --no-header-files --no-man-pages --module-path ../jmods --add-modules java.base,java.datatransfer,java.desktop,java.management,java.net.http,java.security.jgss,java.sql,java.sql.rowset,java.xml,jdk.net,jdk.unsupported,jdk.unsupported.desktop,jdk.xml.dom
# rm $SCRIPTPATH/vendor/linux/amazon-corretto-11-x64-linux-jdk.tar.gz
# rm -rdf $SCRIPTPATH/vendor/linux/amazon-corretto-*-linux-x64

# %userprofile%\AppData\Local\Temp
# "C:\Users\$($_.name)\appdata\local\temp"

#Download JRE
$jreTestPath = [IO.Path]::Combine($jrePath, 'bin', 'javaw.exe')
If (-Not (Test-Path $jreTestPath)) {
    $url= "https://corretto.aws/downloads/latest/amazon-corretto-11-x64-windows-jdk.zip"
    Write-Host "Downloading $filename..."
    # $filepath = [IO.Path]::Combine((get-item $binPath).parent.parent.FullName, 'tmp', 'jre.zip') 
    $tmpDir = [IO.Path]::Combine($Env:USERPROFILE, "appdata\local\temp") 
    $filePath = [IO.Path]::Combine($tmpDir, 'jre.zip') 
    #Invoke-WebRequest -Uri $url -OutFile $filepath
    Set-Location -Path $tmpDir
    Write-Host "Extracting zipped JDK..."
    Expand-Archive $filepath     
    Write-Host "Generating optimized Java runtime..."
    $tmpJdkDir = Get-ChildItem -Directory -Path [IO.Path]::Combine($tmpDir, "jre")  | Select-Object -ExpandProperty FullName
    Write-Host $tmpJdkDir
    #Expand-Archive $filepath -DestinationPath $jrePath
    # $jdkDir = Get-ChildItem -Directory -Path $jrePath | Select-Object -ExpandProperty FullName
    # Get-ChildItem -Path $jdkDir | Copy-Item -Recurse  -Destination $jrePath -Container
} 

#Cleanup
# Get-ChildItem -Path $PSScriptRoot -exclude appJar | Where-Object{ $_.PSIsContainer } | ForEach-Object { Remove-Item -Path $_.FullName -Recurse -Force -Confirm:$false}
# Get-ChildItem -Path $PSScriptRoot\* -include *.txt,*.cmd | ForEach-Object { Remove-Item -Path $_.FullName }
# Get-ChildItem -Path $binPath\* -include *.ps1,*.cmd,*.sample,*.sh,*-sample.xml,*.vbs,*.exe,*.zip,*.pdf | ForEach-Object { Remove-Item -Path $_.FullName }
# $pythonExe = [IO.Path]::Combine($pythonPath, 'python.exe')
# If (Test-Path $pythonExe) {Rename-Item -Path $pythonExe -NewName "python3.exe"}

