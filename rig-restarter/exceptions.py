import log

class RRException(Exception):
  """
  Base exception thrown for rig restarter.
  
  """
  def __init__(self, message):
    log.logger.error(message)


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
