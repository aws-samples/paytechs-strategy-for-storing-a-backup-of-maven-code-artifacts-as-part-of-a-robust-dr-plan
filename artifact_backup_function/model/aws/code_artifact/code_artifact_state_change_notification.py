# coding: utf-8
import pprint

import six

class CodeArtifactChangeNotification(object):


    _types = {
        'repository_name': 'str',
        'package_name': 'str',
        'package_version': 'str',
        'package_format': 'str',
        'domain_owner': 'str',
        'package_version_state': 'str',
        'domain_name': 'str',
        'package_namespace': 'str'
    }

    _attribute_map = {
        'repository_name': 'repositoryName',
        'package_name': 'packageName',
        'package_version': 'packageVersion',
        'package_format': 'packageFormat',
        'domain_owner': 'domainOwner',
        'package_version_state': 'packageVersionState',
        'domain_name': 'domainName',
        'package_namespace': 'packageNamespace'
    }

    def __init__(self, 
                repository_name=None, 
                package_name=None, 
                package_version=None,
                package_format=None,
                domain_owner=None,
                package_version_state=None,
                domain_name=None,
                package_namespace=None):  # noqa: E501
        self._repository_name = None
        self._package_name = None
        self._package_version = None
        self.discriminator = None
        self.repository_name = repository_name
        self.package_name = package_name
        self.package_version = package_version
        self.package_version_state = package_version_state
        self.domain_owner = domain_owner
        self.domain_name = domain_name
        self.package_format = package_format
        self.package_namespace = package_namespace

    @property
    def repository_name(self):
        return self._repository_name

    @repository_name.setter
    def repository_name(self, repository_name):
        self._repository_name = repository_name

    @property
    def package_name(self):

        return self._package_name

    @package_name.setter
    def package_name(self, package_name):


        self._package_name = package_name

    @property
    def package_version(self):
        return self._package_version

    @package_version.setter
    def package_version(self, package_version):


        self._package_version = package_version


    @property
    def domain_owner(self):
        return self._domain_owner
    
    @domain_owner.setter
    def domain_owner(self, domain_owner):


        self._domain_owner = domain_owner

    @property
    def package_version_state(self):
        return self._package_version_state
    
    @package_version_state.setter
    def package_version_state(self, package_version_state):


        self._package_version_state = package_version_state

    @property
    def domain_name(self):
        return self._domain_name
    
    @domain_name.setter
    def domain_name(self, domain_name):


        self._domain_name = domain_name


    @property
    def package_format(self):
        return self._package_format

    @package_format.setter
    def package_format(self, package_format):


        self._package_format = package_format

    @property
    def package_namespace(self):
        return self._package_namespace

    @package_namespace.setter
    def package_namespace(self, package_namespace):


        self._package_namespace = package_namespace

    def to_dict(self):
        result = {}

        for attr, _ in six.iteritems(self._types):
            value = getattr(self, attr)
            if isinstance(value, list):
                result[attr] = list(map(
                    lambda x: x.to_dict() if hasattr(x, "to_dict") else x,
                    value
                ))
            elif hasattr(value, "to_dict"):
                result[attr] = value.to_dict()
            elif isinstance(value, dict):
                result[attr] = dict(map(
                    lambda item: (item[0], item[1].to_dict())
                    if hasattr(item[1], "to_dict") else item,
                    value.items()
                ))
            else:
                result[attr] = value
        if issubclass(CodeArtifactChangeNotification, dict):
            for key, value in self.items():
                result[key] = value

        return result

    def to_str(self):
        return pprint.pformat(self.to_dict())

    def __repr__(self):
        return self.to_str()

    def __eq__(self, other):
        if not isinstance(other, CodeArtifactChangeNotification):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other