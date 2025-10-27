# To learn more about how to use Nix to configure your environment
# see: https://firebase.google.com/docs/studio/customize-workspace
{
  # Which nixpkgs channel to use.
  channel = "stable-24.05"; # or "unstable"

  # Use https://search.nixos.org/packages to find packages
  pkgs = [
    "python311"
    "python311Packages.pip"
    "nodejs_20"
  ];

  # Sets environment variables in the workspace
  env = {};

  idx = {
    # Search for the extensions you want on https://open-vsx.org/ and use "publisher.id"
    extensions = [
      "ms-python.python"
      "esbenp.prettier-vscode"
    ];

    # Enable previews
    previews = {
      enable = true;
      previews = {
        web = {
          command = ["cd" "webapp" "&&" "npm" "run" "dev" "--" "--port" "$PORT"];
          manager = "web";
        };
        backend = {
          command = ["uvicorn" "gui_server:app" "--host" "0.0.0.0" "--port" "8000"];
          manager = "process";
        };
      };
    };

    # Workspace lifecycle hooks
    workspace = {
      # Runs when a workspace is first created
      onCreate = {
        pip-install = "pip install -r requirements.txt";
        npm-install = "cd webapp && npm install";
      };
      # Runs when the workspace is (re)started
      onStart = {};
    };
  };
}
