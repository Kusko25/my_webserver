# Get the directory of the file
$directory_path = $PSScriptRoot

# Change the working directory to the directory of the file
Set-Location -Path $directory_path

# Define the path to the .vscode json file
$vscode_json_path = "launch.json"
$vscode_json_path = Join-Path -Path $directory_path -ChildPath $vscode_json_path

# Check if the .vscode json file exists
if (Test-Path -Path $vscode_json_path) {
    # Read the .vscode json file
    $json_content = Get-Content -Path $vscode_json_path | ConvertFrom-Json
    $config = $json_content.configurations[0]

    # Get the name of the first configuration
    $config_name = $config.name
    
    $config_python_path = Join-Path -Path $directory_path -ChildPath $config.python_path
    # Resolve path
    $config_python_path = Resolve-Path -Path $config_python_path

    # Script path
    $config_script_path = Join-Path -Path $directory_path -ChildPath $config.program

    $config_args = $config.args

    # Run the configuration
    Write-Output "Running configuration: $config_name with"
    $validates = Test-Path -Path $config_python_path
    Write-Output "Python path: $config_python_path ($validates)"
    $validates = Test-Path -Path $config_script_path
    Write-Output "Script path: $config_script_path ($validates)"
    Write-Output "Arguments: $config_args"
    Write-Output "Combined command: $config_python_path $config_script_path $config_args"
    Write-Output "In directory: $directory_path"
    # Run the command
    & $config_python_path $config_script_path $config_args
} else {
    Write-Output "The .vscode json file does not exist."
}