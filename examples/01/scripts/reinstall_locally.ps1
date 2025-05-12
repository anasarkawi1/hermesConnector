#
# Local reinstallation script.
# By Anas Arkawi, 2025.
#


# Try to find the .whl file from the dist folder
$folder = ".\..\..\..\dist"
$firstFile = Get-ChildItem -Path $folder -Filter *.whl -File | Select-Object -First 1



if ($firstFile) {
    Write-Host "Found wheel file: $($firstFile.name)"
    $relativePath = $folder + "\" + $firstFile.name
    Write-Host "Starting installation procedure..."
    pip uninstall hermesConnector
    pip install $relativePath
    Write-Host "Script finished. Exiting."
} else {
    Write-Host "No wheel files found in $folder"
}