import os
def require_gdrive(drivepath = "/content/drive/", verbose=False):
  if not  os.path.exists(drivepath):
    from google.colab import drive
    drive.mount("/content/drive")
  else:
    if verbose:
      print("Google drive already mounted.")
