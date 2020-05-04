from typing import List

from sshtunnel import SSHTunnelForwarder
import json


class SshTunnelConfig():
    def __init__(self, jsonConfig: dict):
        self.remotePort: int = jsonConfig['remotePort']
        self.localPort: int = jsonConfig['localPort']


class SshTunnelManagerConfig():
    def __init__(self, jsonConfig: dict):
        self.host: str = jsonConfig['host']
        self.port: int = jsonConfig['port']
        self.username: str = jsonConfig['username']
        self.password: str = jsonConfig['password']
        self.tunnels: List[SshTunnelConfig] = []
        for tunnelConfig in jsonConfig['tunnels']:
            self.tunnels.append(SshTunnelConfig(tunnelConfig))


class Configuration():
    def __init__(self, filePath: str, autoLoad=True):
        self.filePath = filePath
        self.managers: List[SshTunnelManagerConfig] = []
        if autoLoad:
            self.load()

    def load(self):
        f = open(self.filePath, 'r')
        conf = json.load(f)

        for managerConfig in conf['managers']:
            self.managers.append(SshTunnelManagerConfig(managerConfig))

        f.close()


class SshTunell():
    def __init__(self, remotePort: int, localPort: int):
        self.remotePort = remotePort
        self.localPort = localPort

    def open(self):
        self.tunnel.start()
        print('[+] Tunnel {}:{} started'.format(self.localPort, self.remotePort))

    def close(self):
        self.tunnel.stop()
        print('[+] Tunnel {}:{} closed'.format(self.localPort, self.remotePort))

    def __eq__(self, value):
        return self.localPort == value.localPort and self.remotePort == value.remotePort


class SshTunnelMannager():
    def __init__(self, sshHost: str, sshPort: int, sshUsername: str, sshPassword: str):
        self.tunnels: List[SshTunell] = []
        self.sshHost = sshHost
        self.sshPort = sshPort
        self.sshUsername = sshUsername
        self.sshPassword = sshPassword
        self.connection: SSHTunnelForwarder = None
        self.isActive = False

    def createTunnel(self, remotePort: int, localPort: int) -> SshTunell:
        if self.isActive:
            return None

        tunnel = SshTunell(remotePort, localPort)
        self.tunnels.append(tunnel)
        return tunnel

    def removeTunnel(self, tunnel: SshTunell):
        if self.isActive:
            return

        self.tunnels.remove(tunnel)

    def removeTunnelAt(self, index: int):
        if self.isActive:
            return

        self.tunnels.pop(index)

    def openTunnels(self):
        remote_bind_addresses = []
        local_bind_addresses = []

        for tunnel in self.tunnels:
            remote_bind_addresses.append(('127.0.0.1', tunnel.remotePort))
            local_bind_addresses.append(('127.0.0.1', tunnel.localPort))

        self.connection = SSHTunnelForwarder(
            ssh_address_or_host=(self.sshHost, self.sshPort),
            ssh_username=self.sshUsername,
            ssh_password=self.sshPassword,
            remote_bind_addresses=remote_bind_addresses,
            local_bind_addresses=local_bind_addresses
        )

        self.connection.start()
        self.isActive = True

        for tunnel in self.tunnels:
            print('[+] Tunnel {}:{} opened'.format(tunnel.localPort, tunnel.remotePort))

    def closeTunnels(self):
        if not self.isActive:
            return

        self.connection.stop()
        self.isActive = False

        for tunnel in self.tunnels:
            print('[+] Tunnel {}:{} closed'.format(tunnel.localPort, tunnel.remotePort))


class SshTunnelMannagerBuilder():
    @staticmethod
    def createFromConfiguration(configuration: Configuration):
        managers: List[SshTunnelMannager] = []

        for mc in configuration.managers:
            manager = SshTunnelMannager(
                mc.host, mc.port, mc.username, mc.password)
            for tc in mc.tunnels:
                manager.createTunnel(tc.remotePort, tc.localPort)

            managers.append(manager)

        return managers


def main():
    config = Configuration('configuration.json')

    managers = SshTunnelMannagerBuilder.createFromConfiguration(config)

    for manager in managers:
        manager.openTunnels()

    while True:
        cmd = input('Input command: ')
        if cmd == 'stop':
            for manager in managers:
                manager.closeTunnels()
            break

    print('Bye <3')


if __name__ == "__main__":
    main()
