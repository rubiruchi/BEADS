/******************************************************************************
* Author: Samuel Jero <sjero@purdue.edu>
* SDN Switch-Controller Proxy
******************************************************************************/
#ifndef _LISTENER_H
#define _LISTENER_H
#include "sw_proxy.h"
#include "connection.h"
#include <string>
#include <list>
using namespace std;

class Listener{
	public:
		Listener(int lport, int rport, struct sockaddr_in *addr);
		int start();
		int getLport(){return lport;}
		~Listener();
		void join();

	private:
		static void* listen_thread_run(void *arg);
		void run();

		int ctl_num;
		int lport;
		int rport;
		int sock;
		struct sockaddr_in addr;
		pthread_t listen_thread;
		list<Connection*> connections;
};

#endif
