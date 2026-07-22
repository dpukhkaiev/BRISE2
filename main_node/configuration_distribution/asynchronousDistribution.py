from configuration_distribution.distribution_abs import AbstractDistribution
from tools.rabbitmq_common_tools import RabbitMQConnection, publish

class AsynchronousDistribution(AbstractDistribution):

    def __init__(self, config: dict):
        super().__init__(config)

    def handle_configuration_distribution(self, experiment_id, body):

        self.logger.info(f"Worker dispatched asynchronously")

        publish(exchange='get_new_configuration_exchange',
                routing_key=experiment_id,
                body=body)

    def dispatch(self, experiment_id, body):
        self.handle_configuration_distribution(experiment_id, body)

    def first_it(self, experiment_id):
        pass