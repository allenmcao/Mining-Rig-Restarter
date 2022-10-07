import log

class RRException(Exception):
  """
  Base exception thrown for rig restarter.
  
  """
  def __init__(self, message):
    log.logger.error(message)

class RRMalformedJsonException(Exception):
  """
  Exception raised when JSON is missing a required field.

  Attributes:
    key_attribute -- field
  """

  def __init__(self, json_name):
    self.json_name = json_name
    self.message = f"{json_name} JSON does not match required structure and cannot be parsed."
    super().__init__(self.message)


class RRMissingFieldException(Exception):
  """
  Exception raised when JSON is missing a required field.

  Attributes:
    key_attribute -- field
  """

  def __init__(self, json_name, field):
    self.json_name = json_name
    self.field = field
    self.message = f"{json_name} JSON is missing required field {field}."
    super().__init__(self.message)

class RRMissingWorkerException(Exception):
  """
  Exception raised when worker is not found in given API result.

  Attributes:
    key_attribute -- worker_name
  """

  def __init__(self, worker_name):
    self.worker_name = worker_name
    self.message = f"Worker API result does not include worker {worker_name}."
    super().__init__(self.message)

class RRWrongStatusApiException(Exception):
  """
  Exception raised when using status api is not supported/recognized.

  Attributes:
    key_attribute -- status_api
  """

  def __init__(self, status_api):
    self.status_api = status_api
    self.message = f"{status_api} worker is not recognized."
    super().__init__(self.message)

class RRFlexpoolWrongCoinException(Exception):
  """
  Exception raised when using Flexpool and no coin is given.

  Attributes:
    key_attribute -- worker_name
  """

  def __init__(self):
    self.message = f"When using Flexpool, the coin field must be supplied."
    super().__init__(self.message)


class RRMaxRestartFailsException(Exception):
  """
  Exception raised when worker has restarted max_restart_fails times in a row and is still not online.
  Failsafe for extremely unstable rigs.

  Attributes:
    key_attribute -- worker_name, max_restart_fails
  """

  def __init__(self, worker_name, max_restart_fails):
    self.worker_name = worker_name
    self.max_restart_fails = max_restart_fails
    self.message = f"{worker_name} has failed to restart {max_restart_fails} times in a row and is extremely unstable, stopping restarts."
    super().__init__(self.message)
