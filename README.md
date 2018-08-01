# pixiedust_rosie
Integrate Rosie Pattern Language into a "wrangle data" capability

## Getting started

* Create a Jupyter notebook in your local environment
* Install the [`pixiedust`](https://pypi.org/project/pixiedust/), [`rosie`](https://pypi.org/project/rosie/) and [`pixieduct_rosie`](https://pypi.org/project/pixiedust_rosie/) packages

  ```
  ! pip install pixiedust
  ! pip install rosie
  ! pip install pixiedust_rosie
  ```

* Import `pixiedust_rosie` and call `pixiedust_rosie.wrangle_data`, providing a local or remote URL for a CSV file as parameter

  ```
  import pixiedust_rosie
  pixiedust_rosie.wrangle_data("URL")
  ```
  
  For example:
  ```
  pixiedust_rosie.wrangle_data("https://raw.githubusercontent.com/pixiedust/pixiedust_rosie/master/sample-data/HCUP_Tutorial.csv")
  ```


## License
[Apache 2.0](LICENSE)
