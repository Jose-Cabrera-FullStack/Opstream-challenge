"""
This module defines the Manager class, which handles tasks from an SQS queue.

The Manager class is responsible for:
- Fetching messages from the SQS queue.
- Scheduling tasks based on the messages received.

Example usage:
    async def example_task(arg1, arg2):
        print(f"Task executed with arguments: {arg1}, {arg2}")

    tasks = {
        'example_task': example_task,
    }

    manager = Manager(queue_name='example_queue', tasks=tasks)
    asyncio.run(manager.main())
"""

import json
import asyncio


class Manager:
    """
    Manager class to handle tasks from an SQS queue.

    Attributes:
        queue (str): The name of the SQS queue.
        tasks (dict): A dictionary mapping task names to coroutine functions.
        loop (asyncio.AbstractEventLoop): The event loop for running asynchronous tasks.

    Methods:
        _get_messages(): Asynchronously reads and pops messages from the SQS queue.
        main(): Main loop that continuously fetches messages from the queue and schedules tasks.
    """

    def __init__(self, queue_name: str, tasks: dict):
        self.loop = asyncio.get_event_loop()
        self.queue = queue_name
        self.tasks = tasks

    async def _get_messages(self):
        """Read and pop messages from SQS queue"""
        raise NotImplementedError

    async def main(self):
        """For a given task:
        >>> async def say(something):
        pass
        Messages from queue are expected to have the format:
        >>> message = dict(task='say', args=('something',), kwargs={})
        >>> message = dict(task='say', args=(), kwargs={'something': 'something else'})
        """
        while True:
            messages = await self._get_messages()
            for message in messages:
                body = json.loads(message['Body'])
                task_name = body.get('task')
                args = body.get('args', ())
                kwargs = body.get('kwargs', {})
                task = self.tasks.get(task_name)
                self.loop.create_task(task(*args, **kwargs))
            await asyncio.sleep(1)
