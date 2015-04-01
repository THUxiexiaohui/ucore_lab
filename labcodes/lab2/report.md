# Lab2 report

计23班
谢晓晖 
2012011315

## [练习1]

1.	<b>实现first-fit连续物理内存分配算法。(需要编程)</b>

	> * 在memlayout.h文件中了解了结构体Page的成员基本属性以及参数设置方式
	```
	struct Page {
    	int ref;                        // page frame's reference counter
    	uint32_t flags;                 // array of flags that describe the status of the page frame
    	unsigned int property;          // the num of free block, used in first fit pm manager
    	list_entry_t page_link;         // free list link
	};
	```
	ref属性使用set_page_ref函数进行设置<br/>
	flags的两个标志位，PG_reserved与PG_property使用Set与Clear方法去设为1或者0<br/>

	> * 编写函数default_init
	```
	list_init(&free_list);
    nr_free = 0;
	```
	> * 编写函数default_init_memmap<br/>
	首先将目前page开始的n页进行初始化，对于第一页，将其flags中PG_property位设为1，property属性要设为n，之后将空闲块数量设为n，将第一页加入空闲块链表。
	```
	for (; p != base + n; p ++) {
		ClearPageReserved(p);
		if (p == base) {
			SetPageProperty(p);
			p->property = n;
		} else {
			ClearPageProperty(p);
		}
		set_page_ref(p, 0);
	}
	nr_free += n;
    list_add_before(&free_list, &(base->page_link));
	```
	> * 编写函数default_alloc_pages<br/>
	从free_list里找到第一个符合条件的块fp，若没有直接退出
	```
	struct Page *fp = NULL;
    list_entry_t *le = &free_list;
    while ((le = list_next(le)) != &free_list) {		
        struct Page *p = le2page(le, page_link);
        if (p->property >= n) {
            fp = p;
            break;
        }
    }
    if (fp == NULL) return fp;
	```
	把连续的n个页置为不可被分配，并在free_list中删除该空闲块
	```
    for (i = 0; i < n; ++i) {							
    	struct Page *p = fp + i;
    	SetPageReserved(p);
    	ClearPageProperty(p);
    }
    list_del(le);
	```
	若该空闲块在分配n页后还有剩余remain，则将剩余部分重新加入free_list，并重置该剩余部分的头页，更新总剩余块数并返回
	```
	list_entry_t *lenext = le->next;
	if (remain > 0) {									
    	struct Page *newp = fp + n;
    	SetPageProperty(newp);
    	newp->property = remain;
    	list_add_before(lenext, &(newp->page_link));
    }
    nr_free -= n;
    return fp;
	```

	> * 编写函数default_free_pages<br/>
	将空闲块中的n个连续页置为可用，做法与default_init_memmap中的初始化一致
	```
	struct Page *p = base;
    for (; p != base + n; p ++) {							
        ClearPageReserved(p);
        if (p == base) {
        	SetPageProperty(p);
        	p->property = n;
        } else {
        	ClearPageProperty(p);
        }
        set_page_ref(p, 0);
    }
	```
	再在free_list中找到这个空闲块该插入的位置，位于prevp和nextp之间插入
	```
	list_entry_t *le = &free_list;
    struct Page *prevp, *nextp;
	nextp = le2page(le, page_link);
    while ((le = list_next(le)) != &free_list) {			
    	prevp = nextp;
    	nextp = le2page(le, page_link);
    	if (nextp > base) break;
    }
    list_add_before(le, &(base->page_link));				
	```
	最后判断prevp和nextp的长度，如果可以合并就将后一个的长度加到前一个上，并将后一个销毁
	```
	if (base + base->property == nextp) {					
    	base->property += nextp->property;
    	ClearPageProperty(nextp);
    	list_del(&(nextp->page_link));
    }
    if (prevp + prevp->property == base) {					
    	prevp->property += base->property;
    	ClearPageProperty(base);
    	list_del(&(base->page_link));
    }
    nr_free += n;
	```
2.	<b>你的first fit算法是否有进一步的改进空间？</b>
	> * 用AVL树或者红黑树来代替链表维护空闲块，可以使查找插入和删除的速度得到提升。

### 练习2

1.	<b>实现寻找虚拟地址对应的页表项。(需要编程)</b>
	> * 实现思路：首先是要在一级页表也就是页表目录项当中查找需要的二级页表，如果二级页表不存在我们就尝试create这个项，如果create不成功就return Null，如果可以创建就申请物理内存然后设置标志，按照注释提示对页表项进行清零，另外如果二级页表已经存在那么就计算地址即可。
	> * 实现get_pte函数，根据以下提示内容进行编程：
	```
    pde_t *pdep = &pgdir[PDX(la)];   							   // (1) find page directory entry
    if (!(*pdep & PTE_P)) {                                        // (2) check if entry is not present
        struct Page *page;
        if (!create || (page = alloc_page()) == NULL) {            // (3) check if creating is needed, then alloc page for page table
            return NULL;
        }
        set_page_ref(page, 1);      							   // (4) set page reference
        uintptr_t pa = page2pa(page);							   // (5) get linear address of page
        memset(KADDR(pa), 0, PGSIZE);							   // (6) clear page content using memset							
        *pdep = pa | PTE_U | PTE_W | PTE_P;						   // (7) set page directory entry's permission
    }
    return &((pte_t *)KADDR(PDE_ADDR(*pdep)))[PTX(la)];			   // (8) return page table entry
    ```
	
2.	<b>请描述页目录项（Pag Director Entry）和页表项（Page Table Entry）中每个组成部分的含义和以及对ucore而言的潜在用处。</b>

	> * 页目录项PDE为一个字节32位，前20位为对应页表物理地址的前20位，后12位包含了一些该页目录项的信息，比如保留位、访问位、可写位、权限位等等。
	> * 页表项PTE为一个字节32位，前20位位对应页帧物理地址的前20位，后12位包含了一些该页表项的信息，比如保留位、访问位、可写位、权限位等等。
	> * 页目录项用于一级页表地址与二级页表地址之间的映射，页表项用于二级页表地址与物理地址之间的映射

3.	<b>如果ucore执行过程中访问内存，出现了页访问异常，请问硬件要做哪些事情？</b>

	> * CPU： 产生中断，进入内核态度，进入中断访问例程，执行中断处理程序
	> * 内存、硬盘：导入相应缺失页

### 练习3

1.	<b>释放某虚地址所在的页并取消对应二级页表项的映射。(需要编程)</b>
	> * 实现思路：首先判断这个要移除的页是否存在，如果存在进行下一步的判断，找到这个页的映射项，将该页的被引用的次数减一，若引用次数变成0的话我们就释放该页，同时对tlb进行修改。
	> * 实现get_pte函数，根据以下提示内容进行编程：
	```
    if (*ptep & PTE_P) return				    //(1) check if this page table entry is present
    struct Page *page = pte2page(*ptep);		//(2) find corresponding page to pte
    if (page_ref_dec(page) == 0) {				//(3) decrease page reference
        free_page(page);						//(4) and free this page when page reference reachs 0
    }
    *ptep = 0;									//(5) clear second page table entry
    tlb_invalidate(pgdir, la);					//(6) flush tlb
	```

2.	<b>数据结构Page的全局变量（其实是一个数组）的每一项与页表中的页目录项和页表项有无对应关系？如果有，其对应关系是啥？</b>

	> * 没分配的Page无对应关系；已分配的Page地址的前20位与某些页表项的前20位相等，对应了一个通过页机制转换之前的虚拟地址。

3.	<b>如果希望虚拟地址与物理地址相等，则需要如何修改lab2，完成此事？ </b>

	> * 将KADDR和PADDR改为对等映射

### 与标准答案的差异
---
在练习1中，对于free_list存放的内容与标准答案不同，不同于答案的将所有页同时放入free_list中，本次实验中只将头页放入free_list中。而在之后的合并空闲页中，也采取了较为直观的方式。


### 本实验中重要的知识点
---
1.	最先分配
2.	页模式的机制

### OS原理中很重要但在实验中没有对应上的知识点
---
1.	段机制的部分。
2.	具体整个页映射流程。
3.	具体整个虚拟地址到物理地址映射的流程。
