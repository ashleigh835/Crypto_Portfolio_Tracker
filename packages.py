import sys
import time
import requests
import urllib.parse
import hashlib
import hmac
import base64
import pandas as pd
import json
from cryptography.fernet import Fernet
import os
from requests.auth import AuthBase