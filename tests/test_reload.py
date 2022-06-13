"""
Tests reloading a Slice from a json string.
"""
from crumb.bakery_items.slice import Slice


def test_reload_slice():
    """
    Tests loading a Slice from json and executing it.
    """
    __slice_str = r"""{
  "slice_name": "test",
  "version": 1,
  "input": {
    "objects": {
      "in": "int",
      "in2": "int",
      "in3": "int"
    },
    "mapping": {
      "in": {
        "add15.1654575920572432900": [
          "a"
        ]
      },
      "in2": {
        "minus.1654575920573429700": [
          "a"
        ]
      },
      "in3": {
        "minus.1654575920573429700": [
          "b"
        ]
      }
    }
  },
  "output": {
    "objects": {
      "out": "int",
      "out2": "int"
    },
    "mapping": {
      "out": [
        "minus.1654575920572432900",
        null
      ],
      "out2": [
        "get5.1654575920573429700",
        null
      ]
    }
  },
  "bakery_items": {
    "get5": {
      "bakery_item": "{\"name\": \"get5\", \"executable_file\": \"c:/Users/vroth/Google Drive/Projetos/UoB/breadr/tests/sample_crumbs.py\"}",
      "type": "Crumb"
    },
    "add15": {
      "bakery_item": "{\"name\": \"add15\", \"executable_file\": \"c:/Users/vroth/Google Drive/Projetos/UoB/breadr/tests/sample_crumbs.py\"}",
      "type": "Crumb"
    },
    "minus": {
      "bakery_item": "{\"name\": \"minus\", \"executable_file\": \"c:/Users/vroth/Google Drive/Projetos/UoB/breadr/tests/sample_crumbs.py\"}",
      "type": "Crumb"
    }
  },
  "nodes": {
    "get5.1654575920572432900": {
      "instance_of": "get5",
      "link_str": {
        "input": {},
        "output": {
          "null": {
            "minus.1654575920574429800": [
              "a"
            ]
          }
        }
      },
      "save_exec": true,
      "last_exec": {
        "null": 5
      }
    },
    "add15.1654575920572432900": {
      "instance_of": "add15",
      "link_str": {
        "input": {
          "a": null
        },
        "output": {
          "null": {
            "minus.1654575920574429800": [
              "b"
            ]
          }
        }
      },
      "save_exec": true,
      "last_exec": {
        "null": 16
      }
    },
    "minus.1654575920572432900": {
      "instance_of": "minus",
      "link_str": {
        "input": {
          "a": [
            "minus.1654575920573429700",
            null
          ],
          "b": [
            "minus.1654575920574429800",
            null
          ]
        },
        "output": {}
      },
      "save_exec": true,
      "last_exec": {
        "null": 16
      }
    },
    "get5.1654575920573429700": {
      "instance_of": "get5",
      "link_str": {
        "input": {},
        "output": {}
      },
      "save_exec": true,
      "last_exec": {
        "null": 5
      }
    },
    "minus.1654575920573429700": {
      "instance_of": "minus",
      "link_str": {
        "input": {
          "a": null,
          "b": null
        },
        "output": {
          "null": {
            "minus.1654575920572432900": [
              "a"
            ]
          }
        }
      },
      "save_exec": true,
      "last_exec": {
        "null": 5
      }
    },
    "minus.1654575920574429800": {
      "instance_of": "minus",
      "link_str": {
        "input": {
          "a": [
            "get5.1654575920572432900",
            null
          ],
          "b": [
            "add15.1654575920572432900",
            null
          ]
        },
        "output": {
          "null": {
            "minus.1654575920572432900": [
              "b"
            ]
          }
        }
      },
      "save_exec": true,
      "last_exec": {
        "null": -11
      }
    }
  }
}"""
    slice = Slice(name='dummy')
    slice.from_json(__slice_str)
    ret = slice.run(input={'in': 1, 'in2': 10, 'in3': 5})
    # print(ret)
    assert ret['out'] == 16
    assert ret['out2'] == 5


if __name__ == '__main__':
    test_reload_slice()
