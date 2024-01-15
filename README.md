# GenAi_library

Library to accelerate GenAI projects

##
<div align="center">
  <table><tbody><tr>
      <td align="center"><a href="https://github.com/EYLatamSouth/GenAi_library#installation">
          <img src="/docs/logos/pip.png" alt="Pip" width="128px"><br>
          <strong>Installation</strong>
      </a></td>
      <td align="center"><a href="https://github.com/EYLatamSouth/GenAi_library#first-example">
          <img src="/docs/logos/start.png" alt="First Example" width="128px"><br>
          <strong>First Example</strong>
      </a></td>
      <td align="center"><a href="https://github.com/EYLatamSouth/GenAi_library#tutorials">
          <img src="/docs/logos/steps.png" alt="Tutorials" width="128px"><br>
          <strong>Step by Step Tutorials</strong>
      </a></td>
      <td align="center"><a href="https://github.com/EYLatamSouth/GenAi_library#docs">
          <img src="/docs/logos/paper.png" alt="Documentation" width="128px"><br>
          <strong>Documentation</strong>
      </a></td>
  </tr></tbody></table>
</div>

## 

### Prerequisites

To use the GenAi_library you will need of the libraries listed on the requirements file, and the Azure APIs keys.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Installation

Ensure that your **python** version is >= 3.10 

If you have configured ssh keys from github, you can install directly:

```bash
   $ pip install git+ssh://git@github.com/EYLatamSouth/GenAi_library.git
```

Or you can clone and install the package with the following command:

```bash
   $ git clone https://github.com/EYLatamSouth/GenAi_library.git
   $ cd GenAi_library/
   $ pip install -r requirements.txt
   $ pip install . -U   
```

### First Example

```bash
   $ python src/ey_analytics/apps/main.py
```

## Contributing

Please feel free to propose new features by raising an [Issue](https://github.com/EYLatamSouth/GenAi_library/issues/new/choose) or creating a Pull Request.
