import tomllib

class Repo:
  def __init__(self, name, location):
    self.root =  Path( Path(location)/ name )
    self.src =  Path( self.root, "src", name ) 

  
  def pip_version(self):
      with open(self.root/"pyproject.toml", "rb") as f:
          data = tomllib.load(f)
      return data["project"]["version"]

  def show_config(self):
         with open(self.root/"pyproject.toml", "r") as f:
          print( f.read() )