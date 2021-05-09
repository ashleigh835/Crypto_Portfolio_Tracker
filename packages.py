import sys
import os
import time
import requests
import pandas as pd
import numpy as np
import urllib.parse
import hashlib
import hmac
import base64
import json
from requests.auth import AuthBase
from cryptography.fernet import Fernet