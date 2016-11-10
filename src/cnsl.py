class cnsl:
  """
  Utility class for formatting print statements
  """
  HEADER = '\033[95m'
  OKBLUE = '\033[94m'
  OKGREEN = '\033[92m'
  WARNING = '\033[93m'
  FAIL = '\033[91m'
  ENDC = '\033[0m'
  BOLD = '\033[1m'
  UNDERLINE = '\033[4m'

  @staticmethod
  def debug(msg):
    print(cnsl.HEADER, '$', cnsl.ENDC, msg)

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