using System;
using System.Net.Sockets;

public class ServerConnection
{
    public static Socket ConnectToRemoteServer(string ipAddress, int port)
    {
        Socket client = new Socket(AddressFamily.InterNetwork, SocketType.Stream, ProtocolType.Tcp);
        try
        {
            client.Connect(ipAddress, port);
        }
        catch (Exception)
        {
            // Handle or log the exception as needed
        }
        return client;
    }

    public static Socket ConnectToLocalServer(string pipeName)
    {
        Socket client = new Socket(AddressFamily.Unix, SocketType.Stream, ProtocolType.IP);
        try
        {
            client.Connect("\0" + pipeName);
        }
        catch (Exception)
        {
            // Handle or log the exception as needed
        }
        return client;
    }

    public static void DisconnectFromServer(Socket socket)
    {
        try
        {
            socket.Close();
        }
        catch (Exception)
        {
            // Handle or log the exception as needed
        }
    }
}
