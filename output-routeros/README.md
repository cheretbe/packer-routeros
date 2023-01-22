Packer will create temporary VMs in this dir as it builds boxes.

Deleting this direcory can cause race failures, as multiple packer instances try to create it.
