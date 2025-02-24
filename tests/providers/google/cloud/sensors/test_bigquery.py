# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
from __future__ import annotations

from unittest import mock

import pytest

from airflow.exceptions import AirflowException, TaskDeferred
from airflow.providers.google.cloud.sensors.bigquery import (
    BigQueryTableExistenceAsyncSensor,
    BigQueryTableExistencePartitionAsyncSensor,
    BigQueryTableExistenceSensor,
    BigQueryTablePartitionExistenceSensor,
)
from airflow.providers.google.cloud.triggers.bigquery import (
    BigQueryTableExistenceTrigger,
    BigQueryTablePartitionExistenceTrigger,
)

TEST_PROJECT_ID = "test_project"
TEST_DATASET_ID = "test_dataset"
TEST_TABLE_ID = "test_table"
TEST_GCP_CONN_ID = "test_gcp_conn_id"
TEST_PARTITION_ID = "20200101"
TEST_IMPERSONATION_CHAIN = ["ACCOUNT_1", "ACCOUNT_2", "ACCOUNT_3"]


class TestBigqueryTableExistenceSensor:
    @mock.patch("airflow.providers.google.cloud.sensors.bigquery.BigQueryHook")
    def test_passing_arguments_to_hook(self, mock_hook):
        task = BigQueryTableExistenceSensor(
            task_id="task-id",
            project_id=TEST_PROJECT_ID,
            dataset_id=TEST_DATASET_ID,
            table_id=TEST_TABLE_ID,
            gcp_conn_id=TEST_GCP_CONN_ID,
            impersonation_chain=TEST_IMPERSONATION_CHAIN,
        )
        mock_hook.return_value.table_exists.return_value = True
        results = task.poke(mock.MagicMock())

        assert results is True

        mock_hook.assert_called_once_with(
            gcp_conn_id=TEST_GCP_CONN_ID,
            impersonation_chain=TEST_IMPERSONATION_CHAIN,
        )
        mock_hook.return_value.table_exists.assert_called_once_with(
            project_id=TEST_PROJECT_ID, dataset_id=TEST_DATASET_ID, table_id=TEST_TABLE_ID
        )

    def test_execute_defered(self):
        """
        Asserts that a task is deferred and a BigQueryTableExistenceTrigger will be fired
        when the BigQueryTableExistenceAsyncSensor is executed.
        """
        task = BigQueryTableExistenceSensor(
            task_id="check_table_exists",
            project_id=TEST_PROJECT_ID,
            dataset_id=TEST_DATASET_ID,
            table_id=TEST_TABLE_ID,
            deferrable=True,
        )
        with pytest.raises(TaskDeferred) as exc:
            task.execute(context={})
        assert isinstance(
            exc.value.trigger, BigQueryTableExistenceTrigger
        ), "Trigger is not a BigQueryTableExistenceTrigger"

    def test_excute_defered_failure(self):
        """Tests that an AirflowException is raised in case of error event"""
        task = BigQueryTableExistenceSensor(
            task_id="task-id",
            project_id=TEST_PROJECT_ID,
            dataset_id=TEST_DATASET_ID,
            table_id=TEST_TABLE_ID,
            deferrable=True,
        )
        with pytest.raises(AirflowException):
            task.execute_complete(context={}, event={"status": "error", "message": "test failure message"})

    def test_execute_complete(self):
        """Asserts that logging occurs as expected"""
        task = BigQueryTableExistenceSensor(
            task_id="task-id",
            project_id=TEST_PROJECT_ID,
            dataset_id=TEST_DATASET_ID,
            table_id=TEST_TABLE_ID,
            deferrable=True,
        )
        table_uri = f"{TEST_PROJECT_ID}:{TEST_DATASET_ID}.{TEST_TABLE_ID}"
        with mock.patch.object(task.log, "info") as mock_log_info:
            task.execute_complete(context={}, event={"status": "success", "message": "Job completed"})
        mock_log_info.assert_called_with("Sensor checks existence of table: %s", table_uri)

    def test_execute_defered_complete_event_none(self):
        """Asserts that logging occurs as expected"""
        task = BigQueryTableExistenceSensor(
            task_id="task-id",
            project_id=TEST_PROJECT_ID,
            dataset_id=TEST_DATASET_ID,
            table_id=TEST_TABLE_ID,
        )
        with pytest.raises(AirflowException):
            task.execute_complete(context={}, event=None)


class TestBigqueryTablePartitionExistenceSensor:
    @mock.patch("airflow.providers.google.cloud.sensors.bigquery.BigQueryHook")
    def test_passing_arguments_to_hook(self, mock_hook):
        task = BigQueryTablePartitionExistenceSensor(
            task_id="task-id",
            project_id=TEST_PROJECT_ID,
            dataset_id=TEST_DATASET_ID,
            table_id=TEST_TABLE_ID,
            partition_id=TEST_PARTITION_ID,
            gcp_conn_id=TEST_GCP_CONN_ID,
            impersonation_chain=TEST_IMPERSONATION_CHAIN,
        )
        mock_hook.return_value.table_partition_exists.return_value = True
        results = task.poke(mock.MagicMock())

        assert results is True

        mock_hook.assert_called_once_with(
            gcp_conn_id=TEST_GCP_CONN_ID,
            impersonation_chain=TEST_IMPERSONATION_CHAIN,
        )
        mock_hook.return_value.table_partition_exists.assert_called_once_with(
            project_id=TEST_PROJECT_ID,
            dataset_id=TEST_DATASET_ID,
            table_id=TEST_TABLE_ID,
            partition_id=TEST_PARTITION_ID,
        )

    def test_execute_with_deferrable_mode(self):
        """
        Asserts that a task is deferred and a BigQueryTablePartitionExistenceTrigger will be fired
        when the BigQueryTablePartitionExistenceSensor is executed and deferrable is set to True.
        """
        task = BigQueryTablePartitionExistenceSensor(
            task_id="test_task_id",
            project_id=TEST_PROJECT_ID,
            dataset_id=TEST_DATASET_ID,
            table_id=TEST_TABLE_ID,
            partition_id=TEST_PARTITION_ID,
            deferrable=True,
        )
        with pytest.raises(TaskDeferred) as exc:
            task.execute(context={})
        assert isinstance(
            exc.value.trigger, BigQueryTablePartitionExistenceTrigger
        ), "Trigger is not a BigQueryTablePartitionExistenceTrigger"

    def test_execute_with_deferrable_mode_execute_failure(self):
        """Tests that an AirflowException is raised in case of error event"""
        task = BigQueryTablePartitionExistenceSensor(
            task_id="test_task_id",
            project_id=TEST_PROJECT_ID,
            dataset_id=TEST_DATASET_ID,
            table_id=TEST_TABLE_ID,
            partition_id=TEST_PARTITION_ID,
            deferrable=True,
        )
        with pytest.raises(AirflowException):
            task.execute_complete(context={}, event={"status": "error", "message": "test failure message"})

    def test_execute_complete_event_none(self):
        """Asserts that logging occurs as expected"""
        task = BigQueryTablePartitionExistenceSensor(
            task_id="task-id",
            project_id=TEST_PROJECT_ID,
            dataset_id=TEST_DATASET_ID,
            table_id=TEST_TABLE_ID,
            partition_id=TEST_PARTITION_ID,
            deferrable=True,
        )
        with pytest.raises(AirflowException, match="No event received in trigger callback"):
            task.execute_complete(context={}, event=None)

    def test_execute_complete(self):
        """Asserts that logging occurs as expected"""
        task = BigQueryTablePartitionExistenceSensor(
            task_id="task-id",
            project_id=TEST_PROJECT_ID,
            dataset_id=TEST_DATASET_ID,
            table_id=TEST_TABLE_ID,
            partition_id=TEST_PARTITION_ID,
            deferrable=True,
        )
        table_uri = f"{TEST_PROJECT_ID}:{TEST_DATASET_ID}.{TEST_TABLE_ID}"
        with mock.patch.object(task.log, "info") as mock_log_info:
            task.execute_complete(context={}, event={"status": "success", "message": "test"})
        mock_log_info.assert_called_with(
            'Sensor checks existence of partition: "%s" in table: %s', TEST_PARTITION_ID, table_uri
        )


@pytest.fixture()
def context():
    """
    Creates an empty context.
    """
    context = {}
    yield context


class TestBigQueryTableExistenceAsyncSensor:
    depcrecation_message = (
        "Class `BigQueryTableExistenceAsyncSensor` is deprecated and "
        "will be removed in a future release. "
        "Please use `BigQueryTableExistenceSensor` and "
        "set `deferrable` attribute to `True` instead"
    )

    def test_big_query_table_existence_sensor_async(self):
        """
        Asserts that a task is deferred and a BigQueryTableExistenceTrigger will be fired
        when the BigQueryTableExistenceAsyncSensor is executed.
        """
        with pytest.warns(DeprecationWarning, match=self.depcrecation_message):
            task = BigQueryTableExistenceAsyncSensor(
                task_id="check_table_exists",
                project_id=TEST_PROJECT_ID,
                dataset_id=TEST_DATASET_ID,
                table_id=TEST_TABLE_ID,
            )
        with pytest.raises(TaskDeferred) as exc:
            task.execute(context={})
        assert isinstance(
            exc.value.trigger, BigQueryTableExistenceTrigger
        ), "Trigger is not a BigQueryTableExistenceTrigger"

    def test_big_query_table_existence_sensor_async_execute_failure(self):
        """Tests that an AirflowException is raised in case of error event"""
        with pytest.warns(DeprecationWarning, match=self.depcrecation_message):
            task = BigQueryTableExistenceAsyncSensor(
                task_id="task-id",
                project_id=TEST_PROJECT_ID,
                dataset_id=TEST_DATASET_ID,
                table_id=TEST_TABLE_ID,
            )
        with pytest.raises(AirflowException):
            task.execute_complete(context={}, event={"status": "error", "message": "test failure message"})

    def test_big_query_table_existence_sensor_async_execute_complete(self):
        """Asserts that logging occurs as expected"""
        with pytest.warns(DeprecationWarning, match=self.depcrecation_message):
            task = BigQueryTableExistenceAsyncSensor(
                task_id="task-id",
                project_id=TEST_PROJECT_ID,
                dataset_id=TEST_DATASET_ID,
                table_id=TEST_TABLE_ID,
            )
        table_uri = f"{TEST_PROJECT_ID}:{TEST_DATASET_ID}.{TEST_TABLE_ID}"
        with mock.patch.object(task.log, "info") as mock_log_info:
            task.execute_complete(context={}, event={"status": "success", "message": "Job completed"})
        mock_log_info.assert_called_with("Sensor checks existence of table: %s", table_uri)

    def test_big_query_sensor_async_execute_complete_event_none(self):
        """Asserts that logging occurs as expected"""
        with pytest.warns(DeprecationWarning, match=self.depcrecation_message):
            task = BigQueryTableExistenceAsyncSensor(
                task_id="task-id",
                project_id=TEST_PROJECT_ID,
                dataset_id=TEST_DATASET_ID,
                table_id=TEST_TABLE_ID,
            )
        with pytest.raises(AirflowException):
            task.execute_complete(context={}, event=None)


class TestBigQueryTableExistencePartitionAsyncSensor:
    depcrecation_message = (
        "Class `BigQueryTableExistencePartitionAsyncSensor` is deprecated and "
        "will be removed in a future release. "
        "Please use `BigQueryTableExistencePartitionSensor` and "
        "set `deferrable` attribute to `True` instead"
    )

    def test_big_query_table_existence_partition_sensor_async(self):
        """
        Asserts that a task is deferred and a BigQueryTablePartitionExistenceTrigger will be fired
        when the BigQueryTableExistencePartitionAsyncSensor is executed.
        """
        with pytest.warns(DeprecationWarning, match=self.depcrecation_message):
            task = BigQueryTableExistencePartitionAsyncSensor(
                task_id="test_task_id",
                project_id=TEST_PROJECT_ID,
                dataset_id=TEST_DATASET_ID,
                table_id=TEST_TABLE_ID,
                partition_id=TEST_PARTITION_ID,
            )
        with pytest.raises(TaskDeferred) as exc:
            task.execute(context={})
        assert isinstance(
            exc.value.trigger, BigQueryTablePartitionExistenceTrigger
        ), "Trigger is not a BigQueryTablePartitionExistenceTrigger"

    def test_big_query_table_existence_partition_sensor_async_execute_failure(self):
        """Tests that an AirflowException is raised in case of error event"""
        with pytest.warns(DeprecationWarning, match=self.depcrecation_message):
            task = BigQueryTableExistencePartitionAsyncSensor(
                task_id="test_task_id",
                project_id=TEST_PROJECT_ID,
                dataset_id=TEST_DATASET_ID,
                table_id=TEST_TABLE_ID,
                partition_id=TEST_PARTITION_ID,
            )
        with pytest.raises(AirflowException):
            task.execute_complete(context={}, event={"status": "error", "message": "test failure message"})

    def test_big_query_table_existence_partition_sensor_async_execute_complete_event_none(self):
        """Asserts that logging occurs as expected"""
        with pytest.warns(DeprecationWarning, match=self.depcrecation_message):
            task = BigQueryTableExistencePartitionAsyncSensor(
                task_id="task-id",
                project_id=TEST_PROJECT_ID,
                dataset_id=TEST_DATASET_ID,
                table_id=TEST_TABLE_ID,
                partition_id=TEST_PARTITION_ID,
            )
        with pytest.raises(AirflowException, match="No event received in trigger callback"):
            task.execute_complete(context={}, event=None)

    def test_big_query_table_existence_partition_sensor_async_execute_complete(self):
        """Asserts that logging occurs as expected"""
        with pytest.warns(DeprecationWarning, match=self.depcrecation_message):
            task = BigQueryTableExistencePartitionAsyncSensor(
                task_id="task-id",
                project_id=TEST_PROJECT_ID,
                dataset_id=TEST_DATASET_ID,
                table_id=TEST_TABLE_ID,
                partition_id=TEST_PARTITION_ID,
            )
        table_uri = f"{TEST_PROJECT_ID}:{TEST_DATASET_ID}.{TEST_TABLE_ID}"
        with mock.patch.object(task.log, "info") as mock_log_info:
            task.execute_complete(context={}, event={"status": "success", "message": "test"})
        mock_log_info.assert_called_with(
            'Sensor checks existence of partition: "%s" in table: %s', TEST_PARTITION_ID, table_uri
        )
