# OS Lab3 实验报告

计23
谢晓晖
2012011315

### 练习1
---
1.	<b>完成do_pgfault（mm/vmm.c）函数，给未被映射的地址映射上物理页。</b>

	> * 根据提示完成代码
	> * (1) try to find a pte, if pte's PT(Page Table) isn't existed, then create a PT.<br/>
	用提示中的get_pte函数，由于需要新建，因此最后一个参数为1
	```
	ptep = get_pte(mm->pgdir, addr, 1);
	```
	> * (2) if the phy addr isn't exist, then alloc a page & map the phy addr with logical addr
	```
	if (*ptep == 0) {
    	pgdir_alloc_page(mm->pgdir, addr, perm);
    }
	```

2.	<b>请描述页目录项（Pag Director Entry）和页表（Page Table Entry）中组成部分对ucore实现页替换算法的潜在用处。</b>

	> 页目录项和页表项除了提供地址信息，剩下的某些位提供了其他信息；比如某一位提示了这个页表项对应的是物理内存地址，还是虚拟存储的磁盘位置。同时，页表项中的其他位可以包含一些额外信息，比如时钟算法，在页表项中就能用一位访问位作为该页的标记，记录该页是否被修改；而LRU算法则需要更多的位来支持这一点

3.	<b>如果ucore的缺页服务例程在执行过程中访问内存，出现了页访问异常，请问硬件要做哪些事情？</b>

	> CPU会再次进入中断服务例程，内存堆栈中会再次压入数据维护中断现场

### 练习2
---
1.	<b>完成vmm.c中的do_pgfault函数。</b>

	> * 根据提示完成代码

	```
	 if(swap_init_ok) {
           struct Page *page=NULL;
                                    //(1）According to the mm AND addr, try to load the content of right disk page
                                    //    into the memory which page managed.
                                    //(2) According to the mm, addr AND page, setup the map of phy addr <---> logical addr
                                    //(3) make the page swappable.
        }
        else {
            cprintf("no swap_init_ok but ptep is %x, failed\n",*ptep);
            goto failed;
        }
	```
	> * 完整代码如下

	```
	 if ((ptep = get_pte(mm->pgdir, addr, 1)) == NULL) {
        cprintf("get_pte in do_pgfault failed\n");
        goto failed;
    }
    
    if (*ptep == 0) { // if the phy addr isn't exist, then alloc a page & map the phy addr with logical addr
        if (pgdir_alloc_page(mm->pgdir, addr, perm) == NULL) {
            cprintf("pgdir_alloc_page in do_pgfault failed\n");
            goto failed;
        }
    }
    	else { // if this pte is a swap entry, then load data from disk to a page with phy addr
           // and call page_insert to map the phy addr with logical addr
        if(swap_init_ok) {
            struct Page *page=NULL;
            if ((ret = swap_in(mm, addr, &page)) != 0) {
                cprintf("swap_in in do_pgfault failed\n");
                goto failed;
            }    
            page_insert(mm->pgdir, page, addr, perm);
            swap_map_swappable(mm, addr, page, 1);
        }
        else {
            cprintf("no swap_init_ok but ptep is %x, failed\n",*ptep);
            goto failed;
        }
   	}
	```

2.	<b>在实现FIFO算法的swap_fifo.c中完成map_swappable函数。</b>

	> * 根据提示完成代码
	> * (1) unlink the earliest arrival page in front of pra_list_head qeueue.<br/>
	前面的代码中已经帮我们取好了两个list_entry_t：head和entry，根据提示，是将entry放于head后面，因此联想到lab2中的list的用法，即
	```
	list_add_after(head, entry);
	```

3.	<b>在实现FIFO算法的swap_fifo.c中完成swap_out_vistim函数。</b>

	> * 根据以下提示完成代码
	
	```
	/*LAB3 EXERCISE 2: YOUR CODE*/ 
     //(1)  unlink the  earliest arrival page in front of pra_list_head qeueue
     //(2)  set the addr of addr of this page to ptr_page
     /* Select the tail */
	```
	
	```
	 list_entry_t *le = head->prev;
     	assert(head!=le);
     	struct Page *p = le2page(le, pra_page_link);
     	list_del(le);
     	assert(p !=NULL);
     	*ptr_page = p;
     	return 0;
	```

4.	<b>如果要在ucore上实现"extended clock页替换算法"，现有的swap_manager框架是否足以支持在ucore中实现此算法？如果是，请给你的设计方案。如果不是，请给出你的新的扩展和基此扩展的设计方案。</b>
	
	> * 现在的框架不足以支持ucore中实现此算法。要实现此算法，必须首先维护一个环形链表，然后维护一个指针，指向目前的页，这个是目前不支持的；还要使用页表项中的若干位记录使用位和修改位；但是显然swap_entry中有几位是可用来扩展的
	> * 需要被换出的页的特征是什么？使用位和修改位都为0
	> * 在ucore中如何判断具有这样特征的页？判断页表项中的特定位
	> * 何时进行换入和换出操作？当出现物理内存分配失败，出现缺页异常时


