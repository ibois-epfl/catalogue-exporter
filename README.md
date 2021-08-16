# CatalogueExporter

A Rhinoceros 3D plugin for exporting point cloud dataset to a [web-based catalogue](https://github.com/ibois-epfl/catalogue-explorer).

## Download and installation

You need to have Rhino 7 installed on your Windows computer

1. Head to the [Release section](https://github.com/ibois-epfl/catalogue-exporter/releases/) of this repo and download the latest *.rhi asset.
2. If open, close Rhino
3. Execute the downloaded file and follow installation steps
4. Start Rhino: the plugin is ready to use.

## Usage

The plugin adds the command: `CatalogueExporter` to Rhino. For now, the use of this command is restricted to the workflow [described here](https://github.com/ibois-epfl/eesd-ibois-scanned-stones-dataset).

In addition, the following commands allow batch execution of some Cockroach commands (execute the given command with same parameters to a set of point clouds):
- Cockroach_MeshPoissonBatch
- Cockroach_ComputeNormalsBatch