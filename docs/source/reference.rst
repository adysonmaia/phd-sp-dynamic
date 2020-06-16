API Reference
===============

Packages
---------

.. autosummary::
   :toctree: _modules

   sp.core
   sp.system_controller
   sp.physical_system
   sp.simulator

Service Placement Optimizers
-----------------------------

.. autosummary::
   :nosignatures:

   ~sp.system_controller.optimizer.cloud.CloudOptimizer
   ~sp.system_controller.optimizer.so_heuristic.SOHeuristicOptimizer
   ~sp.system_controller.optimizer.no_migration.NoMigrationOptimizer
   ~sp.system_controller.optimizer.omitted_migration.OmittedMigrationOptimizer
   ~sp.system_controller.optimizer.soga.optimizer.SOGAOptimizer
   ~sp.system_controller.optimizer.moga.optimizer.MOGAOptimizer
   ~sp.system_controller.optimizer.llc.optimizer.LLCOptimizer