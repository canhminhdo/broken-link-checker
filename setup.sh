#!/bin/bash

# require python >= 3.6
case "$(python --version 2>&1)" in
  *" 3."*)
    pip install bs4
    pip install colorama
    ;;
  *)
    echo "Require Python 3.x version!"
  ;;
esac