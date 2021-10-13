from __future__ import annotations
from .context import code_executor
from .context import exception_utils
from .context import Step
from backends.common.serialization_utils import deserialize_obj, serialize_obj
import azure.functions as func
import azure.functions.blob as blob
import logging
import time


class ExecutionEnvironment:
    """
    Environment for executing code in.
    This includes the namespaces, imports etc.
    TODO: Add imports.
    TODO: Add ability to update namespaces and serialize only diffs.
    """
    def __init__(self, global_namespace : dict = {}, local_namespace : dict = {}):
        self.global_namespace = global_namespace
        self.local_namespace = local_namespace

    @property
    def global_namespace(self) -> dict:
        return self._global_namespace

    @global_namespace.setter
    def global_namespace(self, global_namespace: dict):
        self._global_namespace = global_namespace

    @property
    def local_namespace(self) -> dict:
        return self._local_namespace

    @local_namespace.setter
    def local_namespace(self, local_namespace: dict):
        self._local_namespace = local_namespace


def execute_step(
    input: dict,
    envin: blob.InputStream,
    envout: func.Out[bytes]
) -> str:
    """
    Executes a given Step and returns the produced result and output in stderr, stdout.
    """
    start_time = time.time()
    output_env_size_bytes = 0

    try:
        step : Step = input["step"]
        logging.info(f"Executing Step: {step.name}")

        # Get the execution environment from input
        logging.info(envin)
        if envin is not None:
            envin_serialized = envin.read()
            env : ExecutionEnvironment = deserialize_obj(envin_serialized)
        else:
            env : ExecutionEnvironment = ExecutionEnvironment()

        try:
            # Execute the code from the given Step
            exec_result, stdout, stderr = code_executor.exec_with_output(
                step.code,
                env.global_namespace,
                env.local_namespace)

            # Serialize the exectuion environment and set the output
            env_serialized = serialize_obj(env)
            envout.set(env_serialized)
            output_env_size_bytes = len(env_serialized)

            # Prepare the result
            result = {
                "status": "success",
                "exec_result": exec_result,
                "step_index": step.index,
                "stdout": stdout,
                "stderr": stderr
            }
        except Exception as ex:
            exception_info = exception_utils.get_exception_info()
            result = {
                "status": "fail",
                "reason": "exception",
                "exception": str(ex),
                "info": exception_info
            }
        finally:
            # Measure execution time
            end_time = time.time()
            time_taken_ms = 1000 * (end_time - start_time)

            # Prepare execution stats
            stats = {
                "start_time": start_time,
                "end_time": end_time,
                "time_taken_ms": time_taken_ms,
                "output_env_size_bytes": output_env_size_bytes,
            }

        response_payload = {
            "result": result,
            "stats": stats
        }

        return response_payload
    finally:
        logging.info("Total time taken: %.2f ms", 1000 * (time.time() - start_time))
