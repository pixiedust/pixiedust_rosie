## Installing rosie

The python code in this directory requires rosie to be installed on your
system.  There are several ways to do this.

### Option 1: For use ONLY with python

If you want rosie only for use in python programs, then you can use `pip` to
install rosie.

As of this writing (3 April 2018), rosie is not on [PyPI](http://pypi.org) yet,
but you can build the package yourself and then use `pip` to install it:

	git clone https://github.com/rosie-community/PyPI.git
	cd PyPI
	python setup.py sdist
	python setup.py bdist_wheel
	pip install dist/rosie-1.0.0...x86_64.whl

A big advantage of using `pip` this way is that you can later use `pip uninstall
rosie` to remove the installation.  Another benefit is that these instructions
should work with python 2.7 or with python 3.6, and with `--user` or not.

You can test that the installation worked by running the script `test.sh`.  The
test script will run `python` with a small program that imports `rosie`.  If
your python is installed under a different name, like `python3`, then give that
as an argument to the script.

A successful installation will produce output like this:

```shell 
/tmp$ ./PyPI/test.sh python3

Testing in directory /tmp with Python 3.6.5
ROSIE_VERSION 1.0.0-beta-5
ROSIE_HOME /Users/jjennings/Library/Python/3.6/lib/python/site-packages/rosie/rosie-pattern-language
ROSIE_LIBDIR /Users/jjennings/Library/Python/3.6/lib/python/site-packages/rosie/rosie-pattern-language/rpl
ROSIE_COMMAND 
RPL_VERSION 1.2
ROSIE_LIBPATH /Users/jjennings/Library/Python/3.6/lib/python/site-packages/rosie/rosie-pattern-language/rpl
Installation ok
/tmp$ 
```


### Option 2: For general use

A separate installation of rosie is needed if you want to use the rosie CLI and
REPL, or if you want non-python programs to find and use `librosie`.

#### Installing on OS X with brew

As of this writing (3 April 2018), rosie is not on
[the brew repository](https://brew.sh/) yet, but you can obtain the brew formula
yourself and then use `brew` to install it:

    git clone https://github.com/jamiejennings/homebrew-rosie.git
    brew install homebrew-rosie/rosie.rb

A benefit to using `brew` is that you can later use `brew uninstall rosie` to
remove the installation.

#### Installing on OS X without using brew

It's easy to download and install rosie on OS X.  See
[installing from github](#installing-from-github), below.

#### Installing on Linux

It's easy to download and install rosie on Linux.  See
[installing from github](#installing-from-github), below.

### Installing on Windows

Rosie runs on Windows under the Ubuntu subsystem, which is sometimes called the
_bash subsystem_.  Follow the general instructions below on
[installing from github](#installing-from-github), and be sure to do so while in
`bash`.



### Installing from GitHub

These instructions will install the latest release of rosie.

    git clone https://github.com/jamiejennings/rosie-pattern-language.git
    cd rosie-pattern-language
	make

At this point, you have a working installation in the `rosie-pattern-language`
directory.  You will find useful files as follows:

File            | Path | Description
--------------- | ---- | -----------
rosie           | bin/rosie | executable (the rosie CLI, REPL)
librosie.so     | src/librosie/binaries/librosie.so | shared library (Linux)
librosie.dylib  | src/librosie/binaries/librosie.dylib | shared library (OS X)
rosie.py        | src/librosie/python/rosie.py  | python module for `librosie`
rosie.go        | src/librosie/go/src/rosie/rosie.go  | go module for `librosie`
_pattern library_ | rpl/*   | standard pattern library
_documentation_   | doc/*   | documentation


<p></p>

To install rosie system-wide, follow the steps above to build rosie, and then do:

    make install

You can later use `make uninstall` from the `rosie-pattern-language` directory
to remove the installation.  After a system-wide installation, the
`rosie-pattern-language` directory is no longer needed, *except* that it
contains the makefile needed to run `make uninstall`.


