function set_password_to() {
  export $1=`python -c 'import getpass; print(getpass.getpass("Password: "))'`
}
export PYTHONPATH=.:$PWD/lib:$PWD/local/lib/python2.7/site-packages
