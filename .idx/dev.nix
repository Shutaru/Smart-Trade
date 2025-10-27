# To learn more about how to use Nix to configure your environment
# see: https://firebase.google.com/docs/studio/customize-workspace
{ pkgs, ... }: {
  # Which nixpkgs channel to use.
  channel = "stable-24.05"; # or "unstable"

  # Use https://search.nixos.org/packages to find packages
  packages = [
    pkgs.python311
    pkgs.python311Packages.pip
    pkgs.nodejs_20
  ];

  # Sets environment variables in the workspace
  env = {};

  idx = {
    # Search for the extensions you want on https://open-vsx.org/ and use "publisher.id"
    extensions = [
      "ms-python.python",
      "esbenp.prettier-vscode"
    ];

    # Enable previews
    previews = {
      enable = true;
      previews = {
        web = {
          # Installs dependencies and runs the dev server
          command = [
            "cd" "webapp" "&&" 
            "npm" "install" "&&" 
            "npm" "run" "dev" "--" "--port" "$PORT" "--host" "0.0.0.0"
          ];
          manager = "web";
        };
        backend = {
          # Installs dependencies and runs the FastAPI server
          command = [
            "pip" "install" "-r" "requirements.txt" "&&" 
            "python" "-m" "uvicorn" "gui_server:app" "--host" "0.0.0.0" "--port" "8000" "--reload"
          ];
          manager = "process";
        };
      };
    };
    
    # Workspace lifecycle hooks can be left empty as commands are now in previews
    workspace = {};
  };
}
