# OS Lab4 实验报告
计23班 
谢晓晖
2012011315

### 练习1
---
1.	<b>alloc_proc函数（位于kern/process/proc.c中）负责分配并返回一个新的struct proc_struct结构，用于存储新建立的内核线程的管理信息。ucore需要对这个结构进行最基本的初始化，你需要完成这个初始化过程。</b>

	> * 根据提示中需要初始化的内容进行初始化
	
	```
	proc->state = PROC_UNINIT;
	proc->pid = -1;
	proc->runs = 0;
	proc->kstack = 0;
	proc->need_resched = 0;
	proc->parent = NULL;
	proc->mm = NULL;
	memset(&(proc->context), 0, sizeof(struct context));
	proc->tf = NULL;
	proc->cr3 = boot_cr3;
	proc->flags = 0;
	memset(proc->name, 0, sizeof(proc->name));
	```

2.	<b>请说明proc_struct中```struct context context```和```struct trapframe *tf```成员变量含义和在本实验中的作用是啥？（提示通过看代码和编程调试可以判断出来）</b>
	
	> * struct context context用来保存与进程运行状态相关的一系列寄存器信息，在switch_to即进程切换时使用
	> * struct trapframe *tf指向了一个中断帧，该中断帧是调用系统中断时使用的数据结构。在该实验中，在fork新的内核线程后，加载新用户进程，产生系统中断需要使用
	

### 练习2
---
1.	<b>你需要完成在kern/process/proc.c中的do_fork函数中的处理过程。</b>

	> * 根据提示中需要初始化的内容进行初始化
	> * (1) call alloc_proc to allocate a proc_struct<br/>
	```
	if ((proc = alloc_proc()) == NULL) {
    		goto fork_out;
    	}
	proc->pid = get_pid();
    	proc->parent = current;
	 nr_process++;
	```
	> * (2) call setup_kstack to allocate a kernel stack for child process<br/>
	```
	if (setup_kstack(proc)) {
    		goto bad_fork_cleanup_proc;
    	}
	```
	> * (3) call copy_mm to dup OR share mm according clone_flag<br/>
	```
	if (copy_mm(clone_flags, proc)) {
    		goto bad_fork_cleanup_kstack;
    	}
	```
	> * (4) call copy_thread to setup tf & context in proc_struct<br/>
	(5) insert proc_struct into hash_list && proc_list<br/>
   	(6) call wakup_proc to make the new child process RUNNABLE<br/>

	```
		copy_thread(proc, stack, tf);
    		hash_proc(proc);
    		list_add(&proc_list, &(proc->list_link));
    		wakeup_proc(proc);
	```
	> * (7) set ret vaule using child proc's pid
	```
	ret = proc->pid;
	```

2.	<b>请说明ucore是否做到给每个新fork的线程一个唯一的id？请说明你的分析和理由。</b>

	> * 是。通过查看get_pid函数，可以发现，它每次分配pid的时候，都扫描了整个进程队列，取出从0开始最小的没用过的数字作为新的pid，因此fork新进程的时候都能获得唯一的id。

### 练习3
---
1.	<b>在本实验的执行过程中，创建且运行了几个内核线程？</b>
	
	> *　创建且运行了两个内核线程，分别对应idleproc和initproc
	
2.	<b>语句```local_intr_save(intr_flag);....local_intr_restore(intr_flag);```在这里有何作用？请说明理由。</b>

	> *　这段语句在这里是禁用了硬件中断，保证在进程切换的时间里没有硬件中断产生，使得进程切换能够顺利进行。



