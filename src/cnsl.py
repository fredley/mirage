class cnsl:
  """
  Utility class for formatting print statements
  """
  DEBUG = '\033[95m'
  OKBLUE = '\033[94m'
  OKGREEN = '\033[92m'
  WARNING = '\033[93m'
  FAIL = '\033[91m'
  CYAN = '\033[0;36m'
  LGREEN  = '\033[1;32m'
  ENDC = '\033[0m'

  @staticmethod
  def debug(msg):
    print(cnsl.DEBUG, '$', cnsl.ENDC, msg)

  @staticmethod
  def success(msg):
    print(cnsl.OKGREEN, '✔', cnsl.ENDC, msg)

  @staticmethod
  def ok(msg):
    print(cnsl.OKBLUE, '>', cnsl.ENDC, msg)

  @staticmethod
  def warn(msg):
    print(cnsl.WARNING, '!', cnsl.ENDC, msg)

  @staticmethod
  def error(msg):
    print(cnsl.FAIL, '✘', cnsl.ENDC, msg)

  @staticmethod
  def header():
    print("\n    ==" + cnsl.CYAN + "~~" + cnsl.ENDC + "== " + cnsl.LGREEN + 
      "MIRAGE" + cnsl.ENDC + " ==" + cnsl.CYAN + "~~" + cnsl.ENDC + "==\n")